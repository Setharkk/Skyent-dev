# app/db/repositories/analysis_repository.py
import hashlib
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.analysis import Analysis, SentimentAnalysis, Keyword, Summary


class AnalysisRepository:
    """Dépôt pour gérer les opérations de base de données liées aux analyses."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Génère un hash SHA-256 pour le contenu."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        """Récupère une analyse par son ID."""
        query = select(Analysis).where(Analysis.id == analysis_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_content_hash(self, content_hash: str) -> Optional[Analysis]:
        """Récupère une analyse par le hash de son contenu."""
        query = select(Analysis).where(Analysis.content_hash == content_hash)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_analyses(self, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Liste toutes les analyses, avec pagination."""
        query = select(Analysis).offset(skip).limit(limit).order_by(Analysis.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_analysis(self, content: str) -> Analysis:
        """Crée une nouvelle analyse pour un contenu donné."""
        content_hash = self.generate_content_hash(content)
        
        # Vérifier si l'analyse existe déjà pour ce contenu
        existing = await self.get_by_content_hash(content_hash)
        if existing:
            return existing
        
        # Créer une nouvelle analyse
        analysis = Analysis(
            content_hash=content_hash,
            original_content=content
        )
        self.session.add(analysis)
        await self.session.flush()  # Pour obtenir l'ID généré
        
        return analysis
    
    async def add_sentiment_analysis(self, analysis_id: int, 
                              positive_score: float, negative_score: float,
                              neutral_score: float, compound_score: float) -> SentimentAnalysis:
        """Ajoute une analyse de sentiment à une analyse existante."""
        sentiment = SentimentAnalysis(
            analysis_id=analysis_id,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            compound_score=compound_score
        )
        self.session.add(sentiment)
        await self.session.flush()
        return sentiment
    
    async def add_keyword(self, analysis_id: int, text: str, score: float) -> Keyword:
        """Ajoute un mot-clé à une analyse existante."""
        keyword = Keyword(
            analysis_id=analysis_id,
            text=text,
            score=score
        )
        self.session.add(keyword)
        await self.session.flush()
        return keyword
    
    async def add_summary(self, analysis_id: int, text: str) -> Summary:
        """Ajoute un résumé à une analyse existante."""
        summary = Summary(
            analysis_id=analysis_id,
            text=text
        )
        self.session.add(summary)
        await self.session.flush()
        return summary
    
    async def delete_analysis(self, analysis_id: int) -> bool:
        """Supprime une analyse et toutes ses données associées."""
        query = delete(Analysis).where(Analysis.id == analysis_id)
        result = await self.session.execute(query)
        return result.rowcount > 0
