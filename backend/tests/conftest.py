# backend/tests/conftest.py
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Assurez-vous que le répertoire parent est ajouté au chemin Python pour permettre l'importation des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration pour les tests asynchrones
@pytest.fixture(scope="session")
def event_loop():
    """Créer une boucle d'événements pour les tests asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Fixture pour simuler les variables d'environnement pendant les tests
@pytest.fixture(scope="function", autouse=True)
def mock_env_vars():
    """Configurer les variables d'environnement pour les tests."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "LINKEDIN_API_KEY": "test-linkedin-key",
        "TWITTER_API_KEY": "test-twitter-key",
        "FACEBOOK_API_KEY": "test-facebook-key"
    }):
        yield

# Fixture pour les mocks globaux
@pytest.fixture(scope="function", autouse=True)
def mock_external_apis():
    """Mocker les APIs externes pour éviter les appels réseau pendant les tests."""
    with patch("openai.OpenAI"), \
         patch("anthropic.Anthropic"), \
         patch("requests.post"), \
         patch("requests.get"):
        yield
