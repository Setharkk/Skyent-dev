"""Repository pour l'accès aux données du module de génération."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.generation import GeneratedContent


class GenerationRepository:
    """Repository pour l'accès aux données du module de génération."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, generated_content: GeneratedContent) -> GeneratedContent:
        """Créer un nouveau contenu généré."""
        self.session.add(generated_content)
        await self.session.commit()
        await self.session.refresh(generated_content)
        return generated_content
    
    async def get_by_id(self, content_id: str) -> Optional[GeneratedContent]:
        """Récupérer un contenu généré par son ID."""
        stmt = select(GeneratedContent).where(GeneratedContent.id == content_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[GeneratedContent]:
        """Récupérer tous les contenus générés."""
        stmt = select(GeneratedContent)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_with_publications(self, content_id: str) -> Optional[GeneratedContent]:
        """Récupérer un contenu généré avec ses publications associées."""
        stmt = select(GeneratedContent).options(
            selectinload(GeneratedContent.publications)
        ).where(GeneratedContent.id == content_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
