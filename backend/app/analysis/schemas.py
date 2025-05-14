# backend/app/analysis/schemas.py
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, constr, HttpUrl


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


class BriefItem(BaseModel):
    """Schéma pour un élément de brief individuel."""
    title: str
    content: str


class BriefIn(BaseModel):
    """Schéma pour la requête d'analyse de campagne."""
    campaign_name: str
    description: str = ""
    brief_items: List[BriefItem]
    keywords_to_extract: int = Field(default=10, ge=1, le=30)
    summarize: bool = True
    web_search: bool = False
    web_search_results_count: int = Field(default=3, ge=1, le=10)


class WebSearchResult(BaseModel):
    """Schéma pour les résultats de recherche web."""
    title: str
    url: HttpUrl
    snippet: str


class KeywordGroup(BaseModel):
    """Schéma pour un groupe de mots-clés."""
    text: str
    score: float
    frequency: int = 1
    sources: List[str] = []


class BriefItemAnalysis(BaseModel):
    """Schéma pour l'analyse d'un élément de brief."""
    title: str
    keywords: List[KeywordResponse] = []
    summary: Optional[SummaryResponse] = None
    sentiment: Optional[SentimentResponse] = None
    web_results: List[WebSearchResult] = []


class AnalysisOut(BaseModel):
    """Schéma pour la réponse d'analyse de campagne."""
    campaign_id: str
    campaign_name: str
    description: str
    created_at: str
    keywords: List[KeywordGroup] = []
    brief_items_analysis: Dict[str, BriefItemAnalysis] = {}
    global_summary: Optional[str] = None
