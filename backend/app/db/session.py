# app/db/session.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.config import settings


# Créer le moteur SQLAlchemy asynchrone
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    # Utiliser NullPool pour les tests afin d'éviter les connexions persistantes
    poolclass=NullPool if settings.test_database else None,
)

# Créer la factory de session
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    """
    Fournir une session de base de données asynchrone en tant que gestionnaire de contexte.
    À utiliser avec 'async with'.
    """
    session = async_session()
    try:
        yield session
    finally:
        await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dépendance FastAPI pour injecter une session de base de données.
    À utiliser avec FastAPI Depends().
    """
    async with get_session() as session:
        yield session
