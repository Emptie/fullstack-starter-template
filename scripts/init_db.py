#!/usr/bin/env python3
"""Interactive database initialization script.

Prompts for database name and table prefix, creates the database
(if it does not exist), writes configuration to .env, and optionally
creates the first admin user.

Usage:
    uv run python scripts/init_db.py            # full setup
    uv run python scripts/init_db.py --admin-only  # just create an admin user
"""

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"


def load_current_env() -> dict[str, str]:
    """Load current .env values as a dict (simple key=value parser)."""
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, _, value = stripped.partition("=")
                env[key.strip()] = value.strip()
    return env


def prompt(message: str, default: str = "") -> str:
    """Prompt the user for input with a default value."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{message}{suffix}: ").strip()
    return value or default


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Prompt for a yes/no answer."""
    suffix = " [Y/n]" if default else " [y/N]"
    value = input(f"{message}{suffix}: ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


async def create_database_if_needed(
    db_name: str, user: str, password: str, host: str, port: int
) -> None:
    """Connect to postgres maintenance DB and create the target database."""
    conn = await asyncpg.connect(
        user=user, password=password, host=host, port=port, database="postgres"
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            if not db_name.replace("_", "").isalnum():
                print(f"ERROR: Invalid database name '{db_name}'", file=sys.stderr)
                sys.exit(1)
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"  ✓ Created database: {db_name}")
        else:
            print(f"  ✓ Database already exists: {db_name}")
    finally:
        await conn.close()


def write_env(db_name: str, table_prefix: str, existing: dict[str, str]) -> None:
    """Write updated .env file, preserving existing non-DB values."""
    db_keys = {
        "DB_HOST": existing.get("DB_HOST", "localhost"),
        "DB_PORT": existing.get("DB_PORT", "5432"),
        "DB_USER": existing.get("DB_USER", getpass.getuser()),
        "DB_PASSWORD": existing.get("DB_PASSWORD", ""),
        "DB_NAME": db_name,
        "DB_TABLE_PREFIX": table_prefix,
    }

    lines: list[str] = []
    keys_written: set[str] = set()

    # Update existing lines in place
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in db_keys:
                    lines.append(f"{key}={db_keys[key]}")
                    keys_written.add(key)
                    continue
            lines.append(line)

    # Append any DB keys not yet present
    for key, value in db_keys.items():
        if key not in keys_written:
            lines.append(f"{key}={value}")

    # Preserve other existing keys not already in the file
    for key, value in existing.items():
        if key not in db_keys and key not in keys_written:
            lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(lines) + "\n")
    print(f"  ✓ Written: {ENV_FILE}")


async def create_admin_user(
    db_name: str, user: str, password: str, host: str, port: int
) -> None:
    """Interactively create the first admin user."""
    print("\n=== Create Admin Account ===")
    print("You need an admin account to access the admin panel at http://localhost:5174\n")

    admin_name = prompt("Admin name", default="Admin")
    admin_email = prompt("Admin email")
    if not admin_email:
        print("  ⏭ Skipped admin creation (no email provided)")
        return

    admin_password = getpass.getpass("Admin password (input hidden): ")
    if not admin_password:
        print("  ⏭ Skipped admin creation (no password provided)")
        return

    # Hash the password using the same bcrypt as the app
    from starter_shared.security import hash_password

    hashed = hash_password(admin_password)

    conn = await asyncpg.connect(
        user=user, password=password, host=host, port=port, database=db_name
    )
    try:
        # Check if user already exists
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1", admin_email
        )
        if existing:
            # Promote to admin if needed
            await conn.execute(
                "UPDATE users SET role = 'admin' WHERE email = $1 AND role != 'admin'",
                admin_email,
            )
            print(f"  ✓ Admin user already exists: {admin_email}")
        else:
            await conn.execute(
                "INSERT INTO users (email, name, hashed_password, role) VALUES ($1, $2, $3, 'admin')",
                admin_email,
                admin_name,
                hashed,
            )
            print(f"  ✓ Created admin user: {admin_email}")
    finally:
        await conn.close()

    print(f"\n  → Admin panel: http://localhost:5174")
    print(f"  → Login with: {admin_email}")


async def run_init_db() -> None:
    """Full database initialization + optional admin creation."""
    print("=== Fullstack Starter Template — Database Setup ===\n")

    existing = load_current_env()

    db_name = prompt(
        "Database name", default=existing.get("DB_NAME", "starter")
    )
    table_prefix = prompt(
        "Table name prefix (e.g., 'fs_')", default=existing.get("DB_TABLE_PREFIX", "")
    )

    # Credentials: from .env or current OS user
    user = existing.get("DB_USER", getpass.getuser())
    password = existing.get("DB_PASSWORD", "")
    host = existing.get("DB_HOST", "localhost")
    port = int(existing.get("DB_PORT", "5432"))

    print("\nCreating databases...")
    await create_database_if_needed(db_name, user, password, host, port)
    await create_database_if_needed(f"{db_name}_test", user, password, host, port)

    print("\nWriting .env...")
    write_env(db_name, table_prefix, existing)

    effective_url = f"postgresql+asyncpg://{user}:***@{host}:{port}/{db_name}"
    print(f"\n  Database URL: {effective_url}")
    if table_prefix:
        print(f"  Table prefix: {table_prefix} → e.g., '{table_prefix}users'")
    else:
        print("  Table prefix: (none) → e.g., 'users'")

    # Offer to create admin user
    if prompt_yes_no("\nCreate an admin account?", default=True):
        await create_admin_user(db_name, user, password, host, port)

    print("\n✅ Setup complete! Run 'make dev' to start the app.")


async def run_admin_only() -> None:
    """Only create an admin user (skip DB init)."""
    print("=== Create Admin Account ===\n")

    existing = load_current_env()

    db_name = existing.get("DB_NAME", "starter")
    user = existing.get("DB_USER", getpass.getuser())
    password = existing.get("DB_PASSWORD", "")
    host = existing.get("DB_HOST", "localhost")
    port = int(existing.get("DB_PORT", "5432"))

    if not db_name:
        print("ERROR: No database configured. Run 'make dev' first.", file=sys.stderr)
        sys.exit(1)

    await create_admin_user(db_name, user, password, host, port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fullstack Starter Template setup")
    parser.add_argument(
        "--admin-only",
        action="store_true",
        help="Only create an admin user (skip database initialization)",
    )
    args = parser.parse_args()

    if args.admin_only:
        asyncio.run(run_admin_only())
    else:
        asyncio.run(run_init_db())


if __name__ == "__main__":
    main()
