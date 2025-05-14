# backend/app/analysis/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field, constr


class KeywordCreate(BaseModel):
    """Schéma pour la création d'un mot-clé."""
    text: constr(max_length=100)
    score: float = Field(ge=0.0, le=1.0)


class KeywordResponse(BaseModel):
    """Schéma pour la réponse d'un mot-clé."""
    id: int
    text: str
    score: float
    
    class Config:
        from_attributes = True


class SentimentCreateUpdate(BaseModel):
    """Schéma pour la création/mise à jour d'une analyse de sentiment."""
    positive_score: float = Field(ge=0.0, le=1.0)
    negative_score: float = Field(ge=0.0, le=1.0)
    neutral_score: float = Field(ge=0.0, le=1.0)
    compound_score: float = Field(ge=-1.0, le=1.0)


class SentimentResponse(SentimentCreateUpdate):
    """Schéma pour la réponse d'une analyse de sentiment."""
    id: int
    analysis_id: int
    
    class Config:
        from_attributes = True


class SummaryCreateUpdate(BaseModel):
    """Schéma pour la création/mise à jour d'un résumé."""
    text: str


class SummaryResponse(BaseModel):
    """Schéma pour la réponse d'un résumé."""
    id: int
    text: str
    
    class Config:
        from_attributes = True


class AnalysisCreate(BaseModel):
    """Schéma pour la création d'une analyse."""
    content: str


class AnalysisResponse(BaseModel):
    """Schéma pour la réponse d'une analyse."""
    id: int
    content_hash: str
    created_at: str
    sentiment: Optional[SentimentResponse] = None
    keywords: List[KeywordResponse] = []
    summary: Optional[SummaryResponse] = None
    
    class Config:
        from_attributes = True


class ContentAnalysisRequest(BaseModel):
    """Schéma pour la requête d'analyse de contenu."""
    content: str
    analyze_sentiment: bool = True
    extract_keywords: bool = True
    create_summary: bool = True


class ContentAnalysisResponse(BaseModel):
    """Schéma pour la réponse d'analyse de contenu."""
    id: int
    content_hash: str
    sentiment: Optional[SentimentResponse] = None
    keywords: List[KeywordResponse] = []
    summary: Optional[SummaryResponse] = None
