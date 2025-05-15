"""Repository pour l'accès aux données du module de modération."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.moderation import ModerationResult


class ModerationRepository:
    """Repository pour l'accès aux données du module de modération."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, moderation_result: ModerationResult) -> ModerationResult:
        """Créer un nouveau résultat de modération."""
        self.session.add(moderation_result)
        await self.session.commit()
        await self.session.refresh(moderation_result)
        return moderation_result
    
    async def get_by_id(self, moderation_id: str) -> Optional[ModerationResult]:
        """Récupérer un résultat de modération par son ID."""
        stmt = select(ModerationResult).where(ModerationResult.id == moderation_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[ModerationResult]:
        """Récupérer tous les résultats de modération."""
        stmt = select(ModerationResult)
        result = await self.session.execute(stmt)
        return result.scalars().all()
