"""Tests for the scaffold script."""

import subprocess
import sys
from pathlib import Path

import pytest

SCAFFOLD = Path(__file__).resolve().parent.parent / "scaffold.py"


def run_scaffold(*args: str, root: Path) -> subprocess.CompletedProcess:
    """Run scaffold.py as a subprocess with the given arguments."""
    return subprocess.run(
        [sys.executable, str(SCAFFOLD), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


def _make_monorepo(tmp_path: Path) -> Path:
    """Create a minimal monorepo directory structure for testing."""
    dirs = [
        "packages/shared-py/src/starter_shared/types",
        "apps/web-backend/app/models",
        "apps/web-backend/app/routes",
        "apps/web-frontend/src/api",
        "apps/web-frontend/src/views",
        "apps/admin-backend/app/models",
        "apps/admin-backend/app/routes",
        "apps/admin-frontend/src/api",
        "apps/admin-frontend/src/views",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path


class TestScaffold:
    def test_create_web_files(self, tmp_path: Path) -> None:
        """Run scaffold with name='blog', verify 5 files created with correct content."""
        root = _make_monorepo(tmp_path)
        result = run_scaffold("blog", root=root)
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Check 5 files exist
        expected_files = [
            root / "packages/shared-py/src/starter_shared/types/blog.py",
            root / "apps/web-backend/app/models/blog.py",
            root / "apps/web-backend/app/routes/blog.py",
            root / "apps/web-frontend/src/api/blog.ts",
            root / "apps/web-frontend/src/views/Blog.vue",
        ]
        for f in expected_files:
            assert f.exists(), f"Expected file {f} was not created"

        # Verify PascalCase in Vue file
        vue_content = (root / "apps/web-frontend/src/views/Blog.vue").read_text()
        assert "Blog" in vue_content

        # Verify shared types content
        shared_content = (root / "packages/shared-py/src/starter_shared/types/blog.py").read_text()
        assert "Pydantic models for Blog feature" in shared_content

        # Verify model content
        model_content = (root / "apps/web-backend/app/models/blog.py").read_text()
        assert "SQLAlchemy model for blog" in model_content
        assert "from starter_shared.database import Base" in model_content

        # Verify route content
        route_content = (root / "apps/web-backend/app/routes/blog.py").read_text()
        assert 'router = APIRouter(prefix="/blog", tags=["blog"])' in route_content

        # Verify output summary
        assert "Created 5 files, skipped 0 files" in result.stdout

    def test_skip_existing_files(self, tmp_path: Path) -> None:
        """Run scaffold twice with same name, verify second run skips all files."""
        root = _make_monorepo(tmp_path)

        # First run
        result1 = run_scaffold("blog", root=root)
        assert result1.returncode == 0
        assert "Created 5 files, skipped 0 files" in result1.stdout

        # Second run
        result2 = run_scaffold("blog", root=root)
        assert result2.returncode == 0
        assert "Created 0 files, skipped 5 files" in result2.stdout
        assert "SKIP:" in result2.stdout

    def test_missing_name_arg(self, tmp_path: Path) -> None:
        """Run scaffold with no arguments, verify it exits with error."""
        root = _make_monorepo(tmp_path)
        result = run_scaffold(root=root)
        assert result.returncode != 0

    def test_invalid_chars_in_name(self, tmp_path: Path) -> None:
        """Run scaffold with name='../etc', verify it exits with error."""
        root = _make_monorepo(tmp_path)
        result = run_scaffold("../etc", root=root)
        assert result.returncode != 0
        assert "invalid name" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_with_admin_flag(self, tmp_path: Path) -> None:
        """Run scaffold with --with-admin, verify 9 files created."""
        root = _make_monorepo(tmp_path)
        result = run_scaffold("blog", "--with-admin", root=root)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Created 9 files, skipped 0 files" in result.stdout

        # Verify admin files exist
        admin_files = [
            root / "apps/admin-backend/app/models/blog.py",
            root / "apps/admin-backend/app/routes/blog.py",
            root / "apps/admin-frontend/src/api/blog.ts",
            root / "apps/admin-frontend/src/views/Blog.vue",
        ]
        for f in admin_files:
            assert f.exists(), f"Expected admin file {f} was not created"

    def test_hyphenated_name(self, tmp_path: Path) -> None:
        """Run scaffold with name='user-profile', verify correct PascalCase in Vue file."""
        root = _make_monorepo(tmp_path)
        result = run_scaffold("user-profile", root=root)
        assert result.returncode == 0, f"stderr: {result.stderr}"

        vue_path = root / "apps/web-frontend/src/views/UserProfile.vue"
        assert vue_path.exists(), "Vue file should use PascalCase name"

        vue_content = vue_path.read_text()
        assert "UserProfile" in vue_content
        assert "user-profile" not in vue_content

        # Verify route uses slug form
        route_path = root / "apps/web-backend/app/routes/user-profile.py"
        assert route_path.exists()
        route_content = route_path.read_text()
        assert 'prefix="/user-profile"' in route_content
