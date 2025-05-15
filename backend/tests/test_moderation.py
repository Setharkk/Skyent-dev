# backend/tests/test_moderation.py
import os
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env pour les tests
load_dotenv()

# Importer les classes et fonctions nécessaires
from app.main import app
from app.moderation.models import ContentType, ModerationType, ModerationRequest

client = TestClient(app)


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY non définie")
def test_openai_moderation():
    """Test de l'API de modération avec OpenAI."""
    # Texte innocent
    response = client.post(
        "/moderation/moderate/text",
        params={
            "content": "Ceci est un texte sans contenu toxique.",
            "moderation_type": ModerationType.OPENAI
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert result["flagged"] is False
    
    # Texte potentiellement toxique
    response = client.post(
        "/moderation/moderate/text",
        params={
            "content": "Je déteste ce produit, c'est de la merde !",
            "moderation_type": ModerationType.OPENAI
        }
    )
    assert response.status_code == 200
    result = response.json()
    # Le résultat peut varier, mais il devrait être flaggé pour langage grossier
    assert "profanity" in result["categories"]


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY non définie")
def test_anthropic_moderation():
    """Test de l'API de modération avec Anthropic."""
    # Texte innocent
    response = client.post(
        "/moderation/moderate/text",
        params={
            "content": "Ceci est un texte sans contenu toxique.",
            "moderation_type": ModerationType.ANTHROPIC
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert result["flagged"] is False
    
    # Texte potentiellement toxique
    response = client.post(
        "/moderation/moderate/text",
        params={
            "content": "Je te déteste, tu es stupide et je vais te frapper !",
            "moderation_type": ModerationType.ANTHROPIC
        }
    )
    assert response.status_code == 200
    result = response.json()
    # Le résultat peut varier, mais il devrait être flaggé pour violence et/ou harcèlement
    assert result["flagged"] is True
    assert any([result["categories"].get("violence"), result["categories"].get("harassment")])


def test_detoxify_moderation():
    """Test de l'API de modération avec Detoxify (local)."""
    # Ce test peut être lent lors du premier chargement du modèle
    
    # Texte innocent
    response = client.post(
        "/moderation/moderate/text",
        params={
            "content": "Ceci est un texte sans contenu toxique.",
            "moderation_type": ModerationType.DETOXIFY
        }
    )
    assert response.status_code == 200
    result = response.json()
    
    # Texte potentiellement toxique (en anglais car Detoxify est principalement entraîné sur l'anglais)
    response = client.post(
        "/moderation/moderate/text",
        params={
            "content": "You are such an idiot, I hate you!",
            "moderation_type": ModerationType.DETOXIFY
        }
    )
    assert response.status_code == 200
    result = response.json()
    # Vérifier que les scores sont renvoyés
    assert "category_scores" in result
    assert len(result["category_scores"]) > 0


def test_combined_moderation():
    """Test de l'API de modération combinée."""
    # Ce test utilise les fournisseurs disponibles
    
    request_data = ModerationRequest(
        content="Tu es vraiment un idiot, je te déteste !",
        content_type=ContentType.TEXT,
        moderation_type=ModerationType.COMBINED,
        include_original_response=True
    ).model_dump()
    
    response = client.post("/moderation/moderate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    # Vérifier la structure de la réponse
    assert "flagged" in result
    assert "categories" in result
    assert "category_scores" in result
    assert "provider" in result
    assert result["provider"] == "combined"


def test_batch_moderation():
    """Test de l'API de modération par lots."""
    contents = [
        "Ceci est un texte normal.",
        "Tu es stupide et je te déteste !",
        "J'adore les chats et les chiens."
    ]
    
    response = client.post(
        "/moderation/moderate/batch",
        json=contents,
        params={"moderation_type": ModerationType.DETOXIFY}
    )
    assert response.status_code == 200
    results = response.json()
    
    # Vérifier que nous avons reçu 3 résultats
    assert len(results) == 3
    
    # Le premier et le troisième devraient être non toxiques
    assert results[0]["flagged"] is False
    assert results[2]["flagged"] is False
    
    # Le deuxième devrait être plus toxique
    # Note: nous ne garantissons pas qu'il sera flaggé car cela dépend des seuils
