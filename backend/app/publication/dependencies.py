"""Factory pour le service de publication."""
from fastapi import Depends

from app.publication.service import PublicationService
from app.db.repositories import PublicationRepository
from app.db.dependencies import get_publication_repository


def get_publication_service(
    publication_repository: PublicationRepository = Depends(get_publication_repository),
) -> PublicationService:
    """Factory pour le service de publication avec dépendance sur le repository."""
    service = PublicationService()
    service.set_repository(publication_repository)
    return service
