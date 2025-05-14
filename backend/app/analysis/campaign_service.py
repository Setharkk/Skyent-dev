"""
Service d'analyse de campagne utilisant spaCy pour l'extraction des mots-clés et sumy pour la génération de résumés.
"""
import uuid
from datetime import UTC, datetime
from typing import List, Dict, Optional
import spacy
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from collections import Counter, defaultdict

from app.analysis.schemas import (
    BriefIn, BriefItem, BriefItemAnalysis, AnalysisOut, 
    KeywordGroup, KeywordResponse, SummaryResponse, WebSearchResult,
    SentimentResponse
)
from app.websearch.service import WebSearchService

# Charger le modèle spaCy pour le français
nlp = spacy.load("fr_core_news_lg")

class CampaignAnalysisService:
    """Service pour l'analyse de campagne."""
    
    def __init__(self, web_search_service: WebSearchService = None):
        """Initialiser le service d'analyse de campagne."""
        self.web_search_service = web_search_service
    
    async def analyze_campaign(self, brief: BriefIn) -> AnalysisOut:
        """
        Analyser une campagne à partir d'un brief.
        
        Args:
            brief: Le brief de la campagne à analyser
            
        Returns:
            L'analyse de la campagne
        """
        # Générer un ID unique pour la campagne
        campaign_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        
        # Analyse pour chaque élément du brief
        brief_items_analysis = {}
        all_keywords = []
        
        for item in brief.brief_items:
            analysis = await self._analyze_brief_item(
                item, 
                brief.keywords_to_extract, 
                brief.summarize,
                brief.web_search,
                brief.web_search_results_count
            )
            brief_items_analysis[item.title] = analysis
            
            # Collecter tous les mots-clés pour l'analyse globale
            if analysis.keywords:
                all_keywords.extend(analysis.keywords)
        
        # Regrouper et compter les mots-clés
        keyword_groups = self._group_keywords(all_keywords)
        
        # Générer un résumé global si nécessaire
        global_summary = None
        if brief.summarize and brief_items_analysis:
            # Concaténer tous les résumés individuels pour créer un résumé global
            all_summaries = " ".join([
                analysis.summary.text 
                for analysis in brief_items_analysis.values() 
                if analysis.summary
            ])
            if all_summaries:
                global_summary = self._generate_summary(all_summaries, 3)  # 3 phrases pour le résumé global
        
        return AnalysisOut(
            campaign_id=campaign_id,
            campaign_name=brief.campaign_name,
            description=brief.description,
            created_at=created_at,
            keywords=keyword_groups,
            brief_items_analysis=brief_items_analysis,
            global_summary=global_summary
        )
    
    async def _analyze_brief_item(
        self, 
        item: BriefItem, 
        num_keywords: int,
        summarize: bool,
        web_search: bool,
        web_search_results_count: int
    ) -> BriefItemAnalysis:
        """Analyser un élément de brief."""
        keywords = []
        summary = None
        sentiment = None  # Pas d'analyse de sentiment pour l'instant
        web_results = []
        
        # Extraction des mots-clés
        extracted_keywords = self._extract_keywords(item.content, num_keywords)
        for i, (text, score) in enumerate(extracted_keywords):
            keywords.append(KeywordResponse(
                id=i+1,  # ID temporaire
                text=text,
                score=score
            ))
        
        # Génération du résumé
        if summarize:
            summary_text = self._generate_summary(item.content)
            if summary_text:
                summary = SummaryResponse(
                    id=1,  # ID temporaire
                    text=summary_text
                )
        
        # Recherche web
        if web_search and self.web_search_service:
            query = f"{item.title} {' '.join([kw.text for kw in keywords[:5]])}"
            search_results = await self.web_search_service.search(query, web_search_results_count)
            for result in search_results:
                web_results.append(WebSearchResult(
                    title=result.get("title", ""),
                    url=result.get("url", "https://example.com"),
                    snippet=result.get("snippet", "")
                ))
        
        return BriefItemAnalysis(
            title=item.title,
            keywords=keywords,
            summary=summary,
            sentiment=sentiment,
            web_results=web_results
        )
    
    def _extract_keywords(self, text: str, num_keywords: int) -> List[tuple]:
        """Extraire les mots-clés d'un texte avec spaCy."""
        doc = nlp(text)
        
        # Filtrer les tokens qui sont des mots significatifs (noms, adjectifs, verbes)
        significant_tokens = [
            token for token in doc 
            if not token.is_stop and not token.is_punct and not token.is_space
            and token.pos_ in ("NOUN", "PROPN", "ADJ", "VERB")
            and len(token.text) > 2
        ]
        
        # Regrouper les tokens par lemme et calculer la fréquence et l'importance
        lemma_groups = defaultdict(list)
        for token in significant_tokens:
            lemma_groups[token.lemma_].append(token)
        
        # Calculer le score pour chaque groupe de lemmes
        keyword_scores = []
        for lemma, tokens in lemma_groups.items():
            # Le score est basé sur la fréquence et l'importance (basée sur la longueur du mot et sa centralité)
            frequency = len(tokens)
            avg_length = sum(len(token.text) for token in tokens) / frequency
            # Normaliser la fréquence entre 0 et 1
            norm_frequency = min(frequency / max(10, len(significant_tokens) * 0.1), 1.0)
            # Le score final est une combinaison de fréquence normalisée et de longueur normalisée
            score = (norm_frequency * 0.7) + (min(avg_length / 20, 1.0) * 0.3)
            
            # Utiliser le texte du premier token comme représentation du groupe
            text = tokens[0].text
            keyword_scores.append((text, score))
        
        # Trier par score décroissant et prendre les N premiers
        sorted_keywords = sorted(keyword_scores, key=lambda x: x[1], reverse=True)
        return sorted_keywords[:num_keywords]
    
    def _generate_summary(self, text: str, sentences_count: int = 5) -> str:
        """Générer un résumé d'un texte avec sumy."""
        if not text.strip():
            return ""
        
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("french"))
            summarizer = LsaSummarizer()
            
            # Extraire le résumé
            summary_sentences = summarizer(parser.document, sentences_count)
            summary = " ".join([str(sentence) for sentence in summary_sentences])
            
            return summary
        except Exception as e:
            # En cas d'erreur avec le tokenizer, retourner un résumé simple basé sur les premières phrases
            # Cette méthode est un fallback si NLTK n'est pas correctement configuré
            sentences = text.split(". ")
            return ". ".join(sentences[:sentences_count]) + ("." if sentences else "")
    
    def _group_keywords(self, keywords: List[KeywordResponse]) -> List[KeywordGroup]:
        """Regrouper les mots-clés similaires."""
        # Compter la fréquence des mots-clés
        keyword_counter = Counter([keyword.text.lower() for keyword in keywords])
        
        # Créer un dictionnaire pour suivre les sources de chaque mot-clé
        keyword_sources = defaultdict(list)
        for keyword in keywords:
            source = getattr(keyword, "source", None)
            if source:
                keyword_sources[keyword.text.lower()].append(source)
        
        # Créer les groupes de mots-clés
        keyword_groups = []
        for text, count in keyword_counter.most_common():
            # Trouver le mot-clé original pour avoir le score
            original_keywords = [k for k in keywords if k.text.lower() == text]
            if original_keywords:
                # Utiliser le score moyen de tous les mots-clés similaires
                avg_score = sum(k.score for k in original_keywords) / len(original_keywords)
                
                keyword_groups.append(KeywordGroup(
                    text=original_keywords[0].text,  # Utiliser la casse du premier mot-clé trouvé
                    score=avg_score,
                    frequency=count,
                    sources=keyword_sources[text]
                ))
        
        return keyword_groups
