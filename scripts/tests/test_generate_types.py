"""Tests for the type-bridge generator's declaration deduplication.

Regression guard for the duplicate-`export interface` bug.

When a Pydantic model references another *exported* model (e.g.
``PaginatedUserResponse`` holds ``list[UserResponse]``), Pydantic inlines the
referenced model into that schema's ``$defs``. The generator then calls
``json-schema-to-typescript`` once per model, so the inlined model is emitted a
second time as an ``export interface`` (the existing dedup only matched
``export type`` aliases, not ``export interface``). The dedup step must collapse
those duplicates so each top-level declaration appears exactly once.
"""

import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_types import deduplicate_declarations  # noqa: E402

_INTERFACE_RE = re.compile(r"^export interface (\w+)", re.MULTILINE)


def _interface_names(ts: str) -> list[str]:
    """All top-level interface names declared in ``ts``, in order."""
    return _INTERFACE_RE.findall(ts)


class TestDeduplicateDeclarations:
    def test_collapses_duplicate_interfaces(self) -> None:
        ts = textwrap.dedent("""\
            export interface UserResponse {
              id: Id;
              email: Email;
            }
            export interface PaginatedUserResponse {
              items: Items;
            }
            export interface UserResponse {
              id: Id;
              email: Email;
            }
        """)
        result = deduplicate_declarations(ts)
        assert _interface_names(result).count("UserResponse") == 1
        assert _interface_names(result).count("PaginatedUserResponse") == 1

    def test_keeps_first_occurrence_drops_later(self) -> None:
        ts = textwrap.dedent("""\
            export interface Foo {
              a: number;
            }
            export interface Foo {
              b: string;
            }
        """)
        result = deduplicate_declarations(ts)
        assert _interface_names(result).count("Foo") == 1
        assert "a: number;" in result
        assert "b: string;" not in result

    def test_skips_full_block_with_nested_braces(self) -> None:
        ts = textwrap.dedent("""\
            export interface Foo {
              bar: {
                baz: string;
              };
            }
            export interface Foo {
              bar: {
                baz: string;
              };
            }
        """)
        result = deduplicate_declarations(ts)
        assert _interface_names(result).count("Foo") == 1

    def test_collapses_duplicate_type_aliases(self) -> None:
        ts = (
            "export type Email = string;\n"
            "export interface Foo {\n  email: Email;\n}\n"
            "export type Email = string;\n"
        )
        result = deduplicate_declarations(ts)
        assert result.count("export type Email = string;") == 1

    def test_preserves_unique_declarations(self) -> None:
        ts = textwrap.dedent("""\
            export type Email = string;
            export interface Foo {
              email: Email;
            }
            export interface Bar {
              email: Email;
            }
        """)
        result = deduplicate_declarations(ts)
        assert set(_interface_names(result)) == {"Foo", "Bar"}
        assert "export type Email = string;" in result
