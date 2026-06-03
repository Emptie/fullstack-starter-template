#!/usr/bin/env python3
"""Scaffold script for creating new feature skeleton files in the fullstack monorepo."""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def to_pascal_case(slug: str) -> str:
    """Convert a kebab-case slug to PascalCase. E.g. 'user-profile' -> 'UserProfile'."""
    return "".join(part.capitalize() for part in slug.split("-"))


def validate_name(name: str) -> None:
    """Validate feature name: only lowercase letters, digits, hyphens. No path traversal."""
    if not name:
        print("Error: name is required", file=sys.stderr)
        sys.exit(1)
    if "/" in name or ".." in name:
        print(f"Error: invalid name '{name}': path traversal not allowed", file=sys.stderr)
        sys.exit(1)
    if not re.fullmatch(r"[a-z0-9-]+", name):
        print(
            f"Error: invalid name '{name}': only lowercase letters, digits, and hyphens are allowed",
            file=sys.stderr,
        )
        sys.exit(1)


def write_file(path: Path, content: str) -> str:
    """Write content to file. Returns 'CREATED' or 'SKIP'."""
    if path.exists():
        print(f"SKIP: {path} already exists")
        return "SKIP"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"CREATED: {path}")
    return "CREATED"


def scaffold(name: str, with_admin: bool = False, root: Path | None = None) -> None:
    """Create skeleton files for a new feature."""
    validate_name(name)

    root = root or ROOT
    slug = name
    pascal = to_pascal_case(name)

    created = 0
    skipped = 0

    # 1. Shared Pydantic types
    content = (
        f'"""Pydantic models for {pascal} feature."""\n'
        "\n"
        "from pydantic import BaseModel\n"
        "\n"
        "\n"
        f"# TODO: Define your {pascal} Pydantic models here\n"
        "# Then add them to __init__.py and EXPORT_MODELS in scripts/generate_types.py\n"
    )
    result = write_file(root / "packages/shared-py/src/starter_shared/types/{slug}.py".replace("{slug}", slug), content)
    if result == "CREATED":
        created += 1
    else:
        skipped += 1

    # 2. Web backend SQLAlchemy model
    content = (
        f'"""SQLAlchemy model for {slug}."""\n'
        "\n"
        "from sqlalchemy import Column, Integer, String\n"
        "from sqlalchemy.orm import DeclarativeBase\n"
        "\n"
        "from starter_shared.database import Base\n"
        "\n"
        "\n"
        f"# TODO: Define your {pascal} SQLAlchemy model here\n"
        f'# Remember to run: cd apps/web-backend && uv run alembic revision --autogenerate -m "add {slug}"\n'
    )
    result = write_file(root / "apps/web-backend/app/models/{slug}.py".replace("{slug}", slug), content)
    if result == "CREATED":
        created += 1
    else:
        skipped += 1

    # 3. Web backend routes
    content = (
        f'"""API routes for {slug}."""\n'
        "\n"
        "from fastapi import APIRouter\n"
        "\n"
        f'router = APIRouter(prefix="/{slug}", tags=["{slug}"])\n'
        "\n"
        "\n"
        f"# TODO: Implement your {pascal} routes here\n"
        "# Register this router in apps/web-backend/app/routes/__init__.py\n"
    )
    result = write_file(root / "apps/web-backend/app/routes/{slug}.py".replace("{slug}", slug), content)
    if result == "CREATED":
        created += 1
    else:
        skipped += 1

    # 4. Web frontend API client
    content = (
        "/**\n"
        f" * API client for {slug}.\n"
        " * Uses generated types from @starter/shared after running `make generate`.\n"
        " */\n"
        "\n"
        f"// TODO: Implement your {pascal} API client functions here\n"
    )
    result = write_file(root / "apps/web-frontend/src/api/{slug}.ts".replace("{slug}", slug), content)
    if result == "CREATED":
        created += 1
    else:
        skipped += 1

    # 5. Web frontend Vue page
    content = (
        "<script setup lang=\"ts\">\n"
        f"// TODO: Implement your {pascal} page component\n"
        "</script>\n"
        "\n"
        "<template>\n"
        "  <div>\n"
        f"    <!-- TODO: Add your {pascal} page content here -->\n"
        "  </div>\n"
        "</template>\n"
    )
    result = write_file(root / "apps/web-frontend/src/views/{pascal}.vue".replace("{pascal}", pascal), content)
    if result == "CREATED":
        created += 1
    else:
        skipped += 1

    # Admin files (if --with-admin)
    if with_admin:
        # 6. Admin backend SQLAlchemy model
        content = (
            f'"""SQLAlchemy model for {slug}."""\n'
            "\n"
            "from sqlalchemy import Column, Integer, String\n"
            "from sqlalchemy.orm import DeclarativeBase\n"
            "\n"
            "from starter_shared.database import Base\n"
            "\n"
            "\n"
            f"# TODO: Define your {pascal} SQLAlchemy model here\n"
            f'# Remember to run: cd apps/web-backend && uv run alembic revision --autogenerate -m "add {slug}"\n'
        )
        result = write_file(root / "apps/admin-backend/app/models/{slug}.py".replace("{slug}", slug), content)
        if result == "CREATED":
            created += 1
        else:
            skipped += 1

        # 7. Admin backend routes
        content = (
            f'"""API routes for {slug}."""\n'
            "\n"
            "from fastapi import APIRouter\n"
            "\n"
            f'router = APIRouter(prefix="/{slug}", tags=["{slug}"])\n'
            "\n"
            "\n"
            f"# TODO: Implement your {pascal} routes here\n"
            "# Register this router in apps/web-backend/app/routes/__init__.py\n"
        )
        result = write_file(root / "apps/admin-backend/app/routes/{slug}.py".replace("{slug}", slug), content)
        if result == "CREATED":
            created += 1
        else:
            skipped += 1

        # 8. Admin frontend API client
        content = (
            "/**\n"
            f" * API client for {slug}.\n"
            " * Uses generated types from @starter/shared after running `make generate`.\n"
            " */\n"
            "\n"
            f"// TODO: Implement your {pascal} API client functions here\n"
        )
        result = write_file(root / "apps/admin-frontend/src/api/{slug}.ts".replace("{slug}", slug), content)
        if result == "CREATED":
            created += 1
        else:
            skipped += 1

        # 9. Admin frontend Vue page
        content = (
            "<script setup lang=\"ts\">\n"
            f"// TODO: Implement your {pascal} page component\n"
            "</script>\n"
            "\n"
            "<template>\n"
            "  <div>\n"
            f"    <!-- TODO: Add your {pascal} page content here -->\n"
            "  </div>\n"
            "</template>\n"
        )
        result = write_file(root / "apps/admin-frontend/src/views/{pascal}.vue".replace("{pascal}", pascal), content)
        if result == "CREATED":
            created += 1
        else:
            skipped += 1

    print(f"Created {created} files, skipped {skipped} files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold new feature skeleton files.")
    parser.add_argument("name", help="Feature name (lowercase letters, digits, hyphens)")
    parser.add_argument("--with-admin", action="store_true", help="Also generate admin-side files")
    parser.add_argument("--root", type=Path, default=None, help="Project root directory (default: auto-detect)")
    args = parser.parse_args()
    scaffold(args.name, with_admin=args.with_admin, root=args.root)


if __name__ == "__main__":
    main()
