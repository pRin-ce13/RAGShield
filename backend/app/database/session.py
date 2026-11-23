"""Database Connection and Asynchronous Session Management for RAGShield.

Uses SQLAlchemy 2.0 AsyncEngine with support for both SQLite (aiosqlite)
for zero-config local development and PostgreSQL (asyncpg) for production.
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import settings

# Ensure data directory exists if using default SQLite database
if settings.is_sqlite:
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)

# Engine connection arguments
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

# Create asynchronous engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=connect_args
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Declarative Base class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an isolated asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Creates all database tables defined in Base metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
