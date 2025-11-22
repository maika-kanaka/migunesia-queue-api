from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from ..config.settings import settings
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    poolclass=NullPool,
    echo=settings.debug,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# In database.py
async def get_raw_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a raw session without automatic transaction handling
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

async def init_database():
    """
    Initialize database tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """
    Close database connections
    """
    await engine.dispose()
