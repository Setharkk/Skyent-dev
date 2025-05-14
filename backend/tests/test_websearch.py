# backend/tests/test_websearch.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.websearch.service import WebSearchService

client = TestClient(app)

# Tests pour le service WebSearch
@pytest.mark.asyncio
async def test_search_with_tavily_api_mock():
    """Test de recherche avec un mock de l'API Tavily"""
    # Préparer les données de test
    test_results = {
        "results": [
            {
                "title": "Résultat de test 1",
                "url": "https://example.com/1",
                "content": "Ceci est un contenu de test pour le premier résultat."
            },
            {
                "title": "Résultat de test 2",
                "url": "https://example.com/2",
                "content": "Ceci est un contenu de test pour le deuxième résultat."
            }
        ]
    }
    
    # Patcher la méthode search du service directement
    with patch('app.websearch.service.TavilyClient', autospec=True) as MockTavilyClient:
        # Configurer le mock
        mock_client_instance = MockTavilyClient.return_value
        mock_client_instance.search.return_value = test_results
        
        # Créer le service avec notre clé API de test
        service = WebSearchService()
        service.tavily_api_key = "test_api_key"
        service.client = mock_client_instance
        
        # Appeler la méthode search
        results = await service.search("requête de test", 2)
        
        # Vérifier que le client a été appelé avec les bons arguments
        mock_client_instance.search.assert_called_once_with(
            query="requête de test",
            max_results=2,
            search_depth="basic"
        )
        
        # Vérifier les résultats
        assert len(results) == 2
        assert results[0]["title"] == "Résultat de test 1"
        assert results[1]["url"] == "https://example.com/2"
        assert "contenu de test" in results[0]["snippet"]

# Test pour l'endpoint de recherche
def test_search_endpoint():
    """Test de l'endpoint de recherche web"""
    # Mock pour simuler la réponse du service
    mock_results = [
        {
            "title": "Résultat API 1",
            "url": "https://example.com/api/1",
            "snippet": "Contenu du résultat API 1"
        },
        {
            "title": "Résultat API 2",
            "url": "https://example.com/api/2",
            "snippet": "Contenu du résultat API 2"
        }
    ]
    
    # Patcher la méthode search du service
    with patch('app.websearch.service.WebSearchService.search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_results
        
        # Appeler l'endpoint
        response = client.post("/websearch/search", json={
            "query": "requête test api",
            "max_results": 2
        })
        
        # Vérifier la réponse
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["title"] == "Résultat API 1"
        assert data["results"][1]["url"] == "https://example.com/api/2"

def test_mock_search_results():
    """Test des résultats simulés quand l'API n'est pas disponible"""
    service = WebSearchService()
    # Simuler que le client n'est pas configuré
    service.client = None
    
    # Appeler la méthode privée qui génère des résultats simulés
    results = service._mock_search_results("test query", 3)
    
    # Vérifier les résultats
    assert len(results) == 3
    for i, result in enumerate(results):
        assert f"Résultat {i+1}" in result["title"]
        assert "example.com" in result["url"]
        assert "test query" in result["snippet"]
