"""Factory pour le service de génération."""
from fastapi import Depends

from app.generation.service import GenerationService
from app.db.repositories import GenerationRepository
from app.db.dependencies import get_generation_repository


def get_generation_service(
    generation_repository: GenerationRepository = Depends(get_generation_repository),
) -> GenerationService:
    """Factory pour le service de génération avec dépendance sur le repository."""
    service = GenerationService()
    service.set_repository(generation_repository)
    return service
