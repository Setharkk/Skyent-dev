"""Repository pour l'accès aux données du module de publication."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.publication import Publication


class PublicationRepository:
    """Repository pour l'accès aux données du module de publication."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, publication: Publication) -> Publication:
        """Créer une nouvelle publication."""
        self.session.add(publication)
        await self.session.commit()
        await self.session.refresh(publication)
        return publication
    
    async def get_by_id(self, publication_id: str) -> Optional[Publication]:
        """Récupérer une publication par son ID."""
        stmt = select(Publication).where(Publication.id == publication_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[Publication]:
        """Récupérer toutes les publications."""
        stmt = select(Publication)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_content_id(self, content_id: str) -> List[Publication]:
        """Récupérer les publications associées à un contenu."""
        stmt = select(Publication).where(Publication.content_id == content_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
