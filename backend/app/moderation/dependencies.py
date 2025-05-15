"""Factory pour le service de modération."""
from fastapi import Depends

from app.moderation.service import ModerationService
from app.db.repositories import ModerationRepository
from app.db.dependencies import get_moderation_repository


def get_moderation_service(
    moderation_repository: ModerationRepository = Depends(get_moderation_repository),
) -> ModerationService:
    """Factory pour le service de modération avec dépendance sur le repository."""
    service = ModerationService()
    service.set_repository(moderation_repository)
    return service
