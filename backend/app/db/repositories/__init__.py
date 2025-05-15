# app/db/repositories/__init__.py
# Ce fichier initialise le module des dépôts (repositories).

from .analysis_repository import AnalysisRepository
from .generation_repository import GenerationRepository
from .moderation_repository import ModerationRepository
from .publication_repository import PublicationRepository

__all__ = [
    "AnalysisRepository",
    "GenerationRepository",
    "ModerationRepository",
    "PublicationRepository"
]
