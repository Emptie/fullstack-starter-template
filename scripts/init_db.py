#!/usr/bin/env python3
"""Interactive database initialization script.

Prompts for database name and table prefix, creates the database
(if it does not exist), and writes configuration to .env.

Usage:
    uv run python scripts/init_db.py
"""

import asyncio
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
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "root",
        "DB_PASSWORD": "123456",
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


async def main() -> None:
    print("=== Fullstack Starter Template — Database Initialization ===\n")

    existing = load_current_env()

    db_name = prompt(
        "Database name", default=existing.get("DB_NAME", "starter")
    )
    table_prefix = prompt(
        "Table name prefix (e.g., 'fs_')", default=existing.get("DB_TABLE_PREFIX", "")
    )

    # Fixed credentials per project convention
    user = "root"
    password = "123456"
    host = "localhost"
    port = 5432

    print("\nCreating databases...")
    await create_database_if_needed(db_name, user, password, host, port)
    await create_database_if_needed(f"{db_name}_test", user, password, host, port)

    print("\nWriting .env...")
    write_env(db_name, table_prefix, existing)

    effective_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    print(f"\n  Database URL: {effective_url}")
    if table_prefix:
        print(f"  Table prefix: {table_prefix} → e.g., '{table_prefix}users'")
    else:
        print("  Table prefix: (none) → e.g., 'users'")

    print("\nDone! Run 'make dev-db' to start PostgreSQL, then 'make dev-be' for the backend.")


if __name__ == "__main__":
    asyncio.run(main())
