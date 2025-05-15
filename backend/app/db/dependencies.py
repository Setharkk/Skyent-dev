"""Fournisseurs de dépendances pour les sessions et repositories."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.db.repositories import (
    GenerationRepository, 
    ModerationRepository, 
    PublicationRepository
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session de base de données asynchrone."""
    async with async_session() as session:
        yield session


def get_generation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> GenerationRepository:
    """Fournit un repository pour le module de génération."""
    return GenerationRepository(session)


def get_moderation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ModerationRepository:
    """Fournit un repository pour le module de modération."""
    return ModerationRepository(session)


def get_publication_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PublicationRepository:
    """Fournit un repository pour le module de publication."""
    return PublicationRepository(session)
