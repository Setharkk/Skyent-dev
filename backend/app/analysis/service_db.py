# backend/app/analysis/service_db.py
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db_session
from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.models.analysis import Analysis, SentimentAnalysis, Keyword, Summary
from .schemas import ContentAnalysisResponse, SentimentResponse, KeywordResponse, SummaryResponse


class AnalysisDBService:
    """Service d'analyse avec support de base de données."""
    
    def __init__(self, session: AsyncSession):
        self.repo = AnalysisRepository(session)
        self.session = session
    
    @classmethod
    def get_service(cls, session: AsyncSession = Depends(get_db_session)):
        """Factory pour créer le service avec injection de dépendance FastAPI."""
        return cls(session)
    
    async def analyze_content(
        self, 
        content: str, 
        analyze_sentiment: bool = True,
        extract_keywords: bool = True,
        create_summary: bool = True
    ) -> ContentAnalysisResponse:
        """
        Analyse un contenu et stocke les résultats en base de données.
        
        Args:
            content: Le contenu à analyser
            analyze_sentiment: Indique s'il faut analyser le sentiment
            extract_keywords: Indique s'il faut extraire des mots-clés
            create_summary: Indique s'il faut créer un résumé
            
        Returns:
            ContentAnalysisResponse: Le résultat de l'analyse
        """
        # Créer ou récupérer l'analyse de base
        analysis = await self.repo.create_analysis(content)
        
        # Initialiser les listes et objets pour la réponse
        sentiment_result = None
        keywords_result = []
        summary_result = None
        
        # Analyser le sentiment si demandé
        if analyze_sentiment:
            # Simuler une analyse de sentiment (à remplacer par une vraie API de NLP)
            pos_score = 0.6  # Simuler un texte plutôt positif
            neg_score = 0.2
            neu_score = 0.2
            compound = 0.4
            
            # Stocker l'analyse de sentiment
            sentiment = await self.repo.add_sentiment_analysis(
                analysis.id, pos_score, neg_score, neu_score, compound
            )
            
            sentiment_result = SentimentResponse(
                id=sentiment.id,
                analysis_id=sentiment.analysis_id,
                positive_score=sentiment.positive_score,
                negative_score=sentiment.negative_score,
                neutral_score=sentiment.neutral_score,
                compound_score=sentiment.compound_score
            )
        
        # Extraire les mots-clés si demandé
        if extract_keywords:
            # Simuler une extraction de mots-clés (à remplacer par une vraie API de NLP)
            # On divise le contenu en mots et on prend les plus longs comme "mots-clés"
            words = content.split()
            # Trier par longueur décroissante et prendre les 5 premiers
            top_words = sorted([(w, len(w)/20) for w in words if len(w) > 3], 
                               key=lambda x: x[1], reverse=True)[:5]
            
            # Stocker les mots-clés
            for word, score in top_words:
                keyword = await self.repo.add_keyword(analysis.id, word, min(score, 1.0))
                keywords_result.append(KeywordResponse(
                    id=keyword.id,
                    text=keyword.text,
                    score=keyword.score
                ))
        
        # Créer un résumé si demandé
        if create_summary:
            # Simuler un résumé (à remplacer par une vraie API de NLP)
            # On prend simplement la première phrase + "..."
            first_sentence = content.split(".")[0] + "..."
            
            # Stocker le résumé
            summary = await self.repo.add_summary(analysis.id, first_sentence)
            summary_result = SummaryResponse(
                id=summary.id,
                text=summary.text
            )
        
        # Valider les changements dans la base de données
        await self.session.commit()
        
        # Construire la réponse
        return ContentAnalysisResponse(
            id=analysis.id,
            content_hash=analysis.content_hash,
            sentiment=sentiment_result,
            keywords=keywords_result,
            summary=summary_result
        )
    
    async def get_analysis_by_id(self, analysis_id: int) -> Optional[Analysis]:
        """
        Récupère une analyse par son ID.
        
        Args:
            analysis_id: L'identifiant de l'analyse
            
        Returns:
            Optional[Analysis]: L'analyse ou None si non trouvée
        """
        return await self.repo.get_by_id(analysis_id)
    
    async def list_analyses(self, skip: int = 0, limit: int = 10) -> List[Analysis]:
        """
        Liste toutes les analyses avec pagination.
        
        Args:
            skip: Le nombre d'éléments à sauter
            limit: Le nombre maximal d'éléments à retourner
            
        Returns:
            List[Analysis]: La liste des analyses
        """
        return await self.repo.list_analyses(skip, limit)
