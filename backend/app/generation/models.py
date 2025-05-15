# backend/app/generation/models.py
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types de contenu pouvant être générés."""
    LINKEDIN_POST = "linkedin_post"
    TWITTER_POST = "twitter_post"
    BLOG_ARTICLE = "blog_article"
    NEWSLETTER = "newsletter"
    EMAIL = "email"
    PRODUCT_DESCRIPTION = "product_description"
    PRESS_RELEASE = "press_release"
    MARKETING_COPY = "marketing_copy"
    SOCIAL_MEDIA_AD = "social_media_ad"
    OTHER = "other"


class ContentTone(str, Enum):
    """Tonalités disponibles pour la génération de contenu."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"
    FRIENDLY = "friendly"
    ENTHUSIASTIC = "enthusiastic"
    INFORMATIVE = "informative"
    PERSUASIVE = "persuasive"
    HUMOROUS = "humorous"
    SERIOUS = "serious"
    AUTHORITATIVE = "authoritative"


class GenerationParameters(BaseModel):
    """Paramètres pour la génération de contenu."""
    content_type: ContentType = Field(description="Type de contenu à générer")
    prompt: str = Field(description="Description ou sujet du contenu à générer")
    keywords: Optional[List[str]] = Field(None, description="Mots-clés à inclure dans le contenu")
    tone: Optional[ContentTone] = Field(None, description="Tonalité du contenu")
    max_length: Optional[int] = Field(None, description="Longueur maximale du contenu en caractères")
    language: Optional[str] = Field("fr", description="Langue du contenu (code ISO, ex: 'fr', 'en')")
    include_hashtags: Optional[bool] = Field(False, description="Inclure des hashtags (pour réseaux sociaux)")
    include_emojis: Optional[bool] = Field(False, description="Inclure des emojis dans le contenu")
    target_audience: Optional[str] = Field(None, description="Description de l'audience cible")
    references: Optional[List[str]] = Field(None, description="Sources ou références à intégrer")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Contexte supplémentaire")


class GeneratedContent(BaseModel):
    """Contenu généré par le service."""
    content_id: str = Field(description="Identifiant unique du contenu généré")
    content_type: ContentType = Field(description="Type de contenu généré")
    content: str = Field(description="Contenu textuel généré")
    variants: Optional[List[str]] = Field(None, description="Variantes alternatives du contenu")
    hashtags: Optional[List[str]] = Field(None, description="Hashtags suggérés (pour réseaux sociaux)")
    title: Optional[str] = Field(None, description="Titre suggéré (pour articles, emails)")
    summary: Optional[str] = Field(None, description="Résumé du contenu")
    parameters: GenerationParameters = Field(description="Paramètres utilisés pour la génération")
    created_at: str = Field(description="Date et heure de génération (format ISO)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées associées au contenu")


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
