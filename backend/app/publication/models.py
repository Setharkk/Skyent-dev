# backend/app/publication/models.py
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class SocialMediaPlatform(str, Enum):
    """Plateformes de médias sociaux supportées."""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    MEDIUM = "medium"
    YOUTUBE = "youtube"


class PublicationRequest(BaseModel):
    """Demande de publication d'un contenu."""
    content_id: str = Field(description="Identifiant du contenu à publier")
    platform: SocialMediaPlatform = Field(description="Plateforme cible pour la publication")
    schedule_time: Optional[str] = Field(None, description="Date et heure de publication planifiée (format ISO)")
    additional_options: Optional[Dict[str, Any]] = Field(None, description="Options supplémentaires spécifiques à la plateforme")


class PublicationStatus(str, Enum):
    """Statuts possibles d'une publication."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class PublicationResult(BaseModel):
    """Résultat d'une opération de publication."""
    publication_id: str = Field(description="Identifiant unique de la publication")
    content_id: str = Field(description="Identifiant du contenu publié")
    platform: SocialMediaPlatform = Field(description="Plateforme où le contenu a été publié")
    status: PublicationStatus = Field(description="Statut de la publication")
    publication_time: Optional[str] = Field(None, description="Date et heure de publication effective (format ISO)")
    platform_post_id: Optional[str] = Field(None, description="Identifiant de la publication sur la plateforme")
    platform_post_url: Optional[str] = Field(None, description="URL de la publication sur la plateforme")
    error_message: Optional[str] = Field(None, description="Message d'erreur en cas d'échec")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées de la publication")


class DirectPublicationRequest(BaseModel):
    """Demande de publication directe (sans contenu pré-généré)."""
    content: str = Field(description="Contenu à publier")
    platform: SocialMediaPlatform = Field(description="Plateforme cible pour la publication")
    title: Optional[str] = Field(None, description="Titre de la publication (si applicable)")
    media_urls: Optional[List[str]] = Field(None, description="URLs des médias à joindre (images, vidéos)")
    schedule_time: Optional[str] = Field(None, description="Date et heure de publication planifiée (format ISO)")
    additional_options: Optional[Dict[str, Any]] = Field(None, description="Options supplémentaires spécifiques à la plateforme")
