# backend/tests/test_campaign_analysis.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.analysis.schemas import BriefIn, BriefItem, WebSearchResult
from app.analysis.campaign_service import CampaignAnalysisService

client = TestClient(app)

# Données de test
TEST_BRIEF = {
    "campaign_name": "Campagne Test",
    "description": "Description de la campagne de test",
    "brief_items": [
        {
            "title": "Article 1",
            "content": "Ceci est un contenu de test pour l'article 1. Il contient quelques mots-clés comme marketing, stratégie et analyse."
        },
        {
            "title": "Article 2",
            "content": "Ceci est un autre contenu pour tester l'extraction des mots-clés et la génération de résumés."
        }
    ],
    "keywords_to_extract": 5,
    "summarize": True,
    "web_search": False,
    "web_search_results_count": 3
}

# Tests
def test_analyse_campaign_endpoint():
    """Test de l'endpoint /analyse_campaign"""
    response = client.post("/analysis/campaign/analyse_campaign", json=TEST_BRIEF)
    assert response.status_code == 200
    data = response.json()
    
    # Vérification des champs de base
    assert "campaign_id" in data
    assert data["campaign_name"] == TEST_BRIEF["campaign_name"]
    assert data["description"] == TEST_BRIEF["description"]
    assert "created_at" in data
    
    # Vérification des analyses
    assert "keywords" in data
    assert "brief_items_analysis" in data
    assert len(data["brief_items_analysis"]) == len(TEST_BRIEF["brief_items"])
    
    for title, analysis in data["brief_items_analysis"].items():
        assert "keywords" in analysis
        assert len(analysis["keywords"]) <= TEST_BRIEF["keywords_to_extract"]
        if TEST_BRIEF["summarize"]:
            assert "summary" in analysis
            assert analysis["summary"] is not None
            assert "text" in analysis["summary"]

@pytest.mark.asyncio
@patch('app.analysis.campaign_service.CampaignAnalysisService._extract_keywords')
@patch('app.analysis.campaign_service.CampaignAnalysisService._generate_summary')
async def test_analyze_brief_item(mock_generate_summary, mock_extract_keywords):
    """Test de la méthode _analyze_brief_item"""
    # Configuration des mocks
    mock_extract_keywords.return_value = [("marketing", 0.9), ("stratégie", 0.8), ("analyse", 0.7)]
    mock_generate_summary.return_value = "Ceci est un résumé de test."
    
    # Créer une instance de service avec un mock de web_search_service
    mock_web_search = MagicMock()
    mock_web_search.search = AsyncMock(return_value=[
        {"title": "Résultat 1", "url": "https://example.com/1", "snippet": "Snippet 1"},
        {"title": "Résultat 2", "url": "https://example.com/2", "snippet": "Snippet 2"}
    ])
    service = CampaignAnalysisService(web_search_service=mock_web_search)
    
    # Appel de la méthode à tester
    brief_item = BriefItem(title="Article Test", content="Contenu de test")
    result = await service._analyze_brief_item(
        brief_item, 
        num_keywords=3,
        summarize=True,
        web_search=True,
        web_search_results_count=2
    )
    
    # Vérification des résultats
    assert result.title == "Article Test"
    assert len(result.keywords) == 3
    assert result.summary is not None
    assert result.summary.text == "Ceci est un résumé de test."
    
    # Vérifier que web_search a bien été appelé
    mock_web_search.search.assert_called_once()
    assert len(result.web_results) == 2

def test_extract_keywords():
    """Test de la méthode _extract_keywords"""
    service = CampaignAnalysisService()
    
    # Texte de test avec des mots-clés évidents
    text = """L'intelligence artificielle est une technologie qui permet aux ordinateurs d'imiter l'intelligence humaine.
              Les applications d'IA incluent la reconnaissance vocale, la vision par ordinateur et le traitement du langage naturel.
              Le machine learning est un sous-domaine de l'IA qui permet aux systèmes d'apprendre sans être explicitement programmés."""
    
    keywords = service._extract_keywords(text, num_keywords=5)
    
    # Vérifications
    assert len(keywords) <= 5
    assert all(isinstance(k, tuple) and len(k) == 2 for k in keywords)
    assert all(isinstance(k[0], str) and isinstance(k[1], float) for k in keywords)
    
    # Les mots-clés devraient inclure des termes comme intelligence, artificielle, machine learning, etc.
    keywords_text = [k[0].lower() for k in keywords]
    possible_keywords = ["intelligence", "artificielle", "technologie", "machine", "learning", "ordinateur"]
    
    # Au moins quelques mots-clés attendus devraient être présents
    assert any(kw in keywords_text for kw in possible_keywords)

def test_generate_summary():
    """Test de la méthode _generate_summary"""
    service = CampaignAnalysisService()
    
    text = """L'intelligence artificielle est une technologie qui permet aux ordinateurs d'imiter l'intelligence humaine.
              Les applications d'IA incluent la reconnaissance vocale, la vision par ordinateur et le traitement du langage naturel.
              Le machine learning est un sous-domaine de l'IA qui permet aux systèmes d'apprendre sans être explicitement programmés.
              Les réseaux de neurones profonds ont révolutionné le domaine de l'IA ces dernières années.
              Les enjeux éthiques de l'IA incluent la vie privée, la sécurité et l'impact sur l'emploi."""
    
    summary = service._generate_summary(text, sentences_count=2)
    
    # Vérifications
    assert summary
    assert isinstance(summary, str)
    assert len(summary.split('.')) <= 3  # 2 phrases + éventuellement une phrase incomplète
