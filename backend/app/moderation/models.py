# backend/app/moderation/models.py
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types de contenu pouvant être modérés."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ModerationType(str, Enum):
    """Types de modération disponibles."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DETOXIFY = "detoxify"
    COMBINED = "combined"


class ToxicityCategory(str, Enum):
    """Catégories de toxicité pouvant être détectées."""
    HATE = "hate"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    PROFANITY = "profanity"
    MISINFORMATION = "misinformation"
    OTHER = "other"


class ModerationResult(BaseModel):
    """Résultat de la modération de contenu."""
    flagged: bool = Field(description="Indique si le contenu a été signalé comme inapproprié")
    categories: Dict[str, bool] = Field(description="Catégories de contenu problématique détectées")
    category_scores: Dict[str, float] = Field(description="Scores de confiance pour chaque catégorie")
    provider: str = Field(description="Fournisseur ayant effectué la modération")
    content_type: ContentType = Field(description="Type de contenu modéré")
    original_response: Optional[Dict[str, Any]] = Field(None, description="Réponse brute du fournisseur")
    moderation_id: Optional[str] = Field(None, description="Identifiant unique du résultat de modération")


class ModerationRequest(BaseModel):
    """Demande de modération de contenu."""
    content: Union[str, List[str]] = Field(description="Contenu à modérer (texte ou liste de textes)")
    content_type: ContentType = Field(default=ContentType.TEXT, description="Type de contenu")
    moderation_type: ModerationType = Field(default=ModerationType.COMBINED, description="Type de modération à utiliser")
    include_original_response: bool = Field(default=False, description="Inclure la réponse brute du fournisseur")
