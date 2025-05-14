# backend/app/websearch/service.py
from typing import List, Dict, Any
import logging
from tavily import TavilyClient
from ..config import settings

class WebSearchService:
    def __init__(self):
        self.tavily_api_key = settings.tavily_api_key
        self.client = None
        if self.tavily_api_key:
            self.client = TavilyClient(api_key=self.tavily_api_key)
        else:
            logging.warning("Tavily API key not set. Using mock search results.")

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Effectue une recherche web en utilisant l'API Tavily.
        
        Args:
            query: Le texte de la recherche
            num_results: Le nombre de résultats à retourner
            
        Returns:
            Une liste de résultats de recherche
        """
        if not self.client:
            # Mode simulé pour les tests ou si la clé API n'est pas configurée
            return self._mock_search_results(query, num_results)
        
        try:
            # Recherche via Tavily API (non-async car l'API Tavily n'est pas async)
            search_response = self.client.search(
                query=query,
                max_results=num_results,
                search_depth="basic"  # basic ou comprehensive selon les besoins
            )
            
            # Formater les résultats
            results = []
            for result in search_response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")
                })
            
            return results
        except Exception as e:
            logging.error(f"Erreur lors de la recherche Tavily: {str(e)}")
            # Fallback aux résultats simulés en cas d'erreur
            return self._mock_search_results(query, num_results)
    
    def _mock_search_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Génère des résultats factices pour les tests ou si l'API est indisponible."""
        return [
            {
                "title": f"Résultat {i+1} pour '{query}'",
                "url": f"https://example.com/result/{i+1}",
                "snippet": f"Ceci est un extrait de texte simulé pour le résultat {i+1} concernant '{query}'."
            } 
            for i in range(min(num_results, 10))
        ]


websearch_service = WebSearchService()
