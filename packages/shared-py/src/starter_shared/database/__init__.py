"""Async SQLAlchemy database setup.

Provides engine, session factory, and base model class.
All backend apps import from here to share the same database configuration.
Table name prefix is automatically applied via the Base class.
"""

import re
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from starter_shared.config import settings

engine = create_async_engine(
    settings.db.effective_database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case.

    Examples: User -> user, UserProfile -> user_profile
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Automatically generates ``__tablename__`` from the class name,
    prepended with the configured ``db_table_prefix``.

    Naming rule: ``{prefix}{snake_case_class_name}s``
    Example with prefix ``fs_``: ``User`` → ``fs_users``
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        if cls.__name__ == "Base":
            return "_base"
        prefix = settings.db.db_table_prefix
        return f"{prefix}{_camel_to_snake(cls.__name__)}s"


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage in routes::

        from typing import Annotated
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession

        from starter_shared.database import get_session

        DbSession = Annotated[AsyncSession, Depends(get_session)]

        @router.get("/users")
        async def list_users(session: DbSession):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
