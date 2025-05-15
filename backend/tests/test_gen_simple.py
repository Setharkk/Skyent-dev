# backend/tests/test_gen_simple.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.generation.service import GenerationService
from app.generation.models import GenerationOptions, GenerationResult, ContentType, GenerationType

# Exemple de données d'entrée
TEST_PROMPT = "Générer un post sur les avantages du développement durable"
TEST_CONTENT_OPENAI = "Le développement durable offre de nombreux avantages pour notre planète."
TEST_CONTENT_ANTHROPIC = "Protéger notre environnement est crucial pour les générations futures."
TEST_CONTENT_GEMINI = "Le développement durable permet de préserver les ressources naturelles."
TEST_CONTENT_OLLAMA = "Adopter des pratiques durables est essentiel pour l'avenir de notre planète."

@pytest.fixture
def mocked_generation_service():
    """Crée une instance du service de génération avec des méthodes mockées."""
    # Crée le service avec de vrais constructeurs
    service = GenerationService()
    
    # Mock les méthodes internes de génération
    service._generate_with_openai = AsyncMock(
        return_value=(TEST_CONTENT_OPENAI, {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30})
    )
    service._generate_with_anthropic = AsyncMock(
        return_value=(TEST_CONTENT_ANTHROPIC, {"input_tokens": 10, "output_tokens": 20})
    )
    service._generate_with_gemini = AsyncMock(
        return_value=(TEST_CONTENT_GEMINI, {"prompt_tokens": 10, "candidate_tokens": 20})
    )
    service._generate_with_ollama = AsyncMock(
        return_value=(TEST_CONTENT_OLLAMA, {})
    )
    
    return service

@pytest.mark.asyncio
async def test_generate_with_openai(mocked_generation_service):
    """Teste la génération avec OpenAI."""
    options = GenerationOptions(
        prompt=TEST_PROMPT,
        generation_type=GenerationType.OPENAI,
        content_type=ContentType.TEXT,
        max_tokens=100
    )
    
    result = await mocked_generation_service.generate_content(
        prompt=TEST_PROMPT,
        options=options
    )
    
    # Vérifie que le résultat est conforme
    assert isinstance(result, GenerationResult)
    assert result.content == TEST_CONTENT_OPENAI
    assert result.provider == "openai"
    assert result.content_type == ContentType.TEXT
    assert "total_tokens" in result.usage
    
    # Vérifie que la méthode interne a été appelée
    mocked_generation_service._generate_with_openai.assert_called_once()

@pytest.mark.asyncio
async def test_generate_with_anthropic(mocked_generation_service):
    """Teste la génération avec Anthropic."""
    options = GenerationOptions(
        prompt=TEST_PROMPT,
        generation_type=GenerationType.ANTHROPIC,
        content_type=ContentType.TEXT,
        max_tokens=100
    )
    
    result = await mocked_generation_service.generate_content(
        prompt=TEST_PROMPT,
        options=options
    )
    
    # Vérifie que le résultat est conforme
    assert isinstance(result, GenerationResult)
    assert result.content == TEST_CONTENT_ANTHROPIC
    assert result.provider == "anthropic"
    assert result.content_type == ContentType.TEXT
    assert "input_tokens" in result.usage
    
    # Vérifie que la méthode interne a été appelée
    mocked_generation_service._generate_with_anthropic.assert_called_once()

@pytest.mark.asyncio
async def test_generation_service_provider_selection(mocked_generation_service):
    """Teste que le service sélectionne le bon fournisseur."""
    
    # Test avec OpenAI
    await mocked_generation_service.generate_content(
        prompt=TEST_PROMPT,
        options=GenerationOptions(generation_type=GenerationType.OPENAI)
    )
    mocked_generation_service._generate_with_openai.assert_called_once()
    
    # Réinitialise les mocks
    mocked_generation_service._generate_with_openai.reset_mock()
    mocked_generation_service._generate_with_anthropic.reset_mock()
    mocked_generation_service._generate_with_gemini.reset_mock()
    mocked_generation_service._generate_with_ollama.reset_mock()
    
    # Test avec Anthropic
    await mocked_generation_service.generate_content(
        prompt=TEST_PROMPT,
        options=GenerationOptions(generation_type=GenerationType.ANTHROPIC)
    )
    mocked_generation_service._generate_with_anthropic.assert_called_once()
    
    # Réinitialise les mocks
    mocked_generation_service._generate_with_openai.reset_mock()
    mocked_generation_service._generate_with_anthropic.reset_mock()
    mocked_generation_service._generate_with_gemini.reset_mock()
    mocked_generation_service._generate_with_ollama.reset_mock()
    
    # Test avec Gemini
    await mocked_generation_service.generate_content(
        prompt=TEST_PROMPT,
        options=GenerationOptions(generation_type=GenerationType.GEMINI)
    )
    mocked_generation_service._generate_with_gemini.assert_called_once()
    
    # Réinitialise les mocks
    mocked_generation_service._generate_with_openai.reset_mock()
    mocked_generation_service._generate_with_anthropic.reset_mock()
    mocked_generation_service._generate_with_gemini.reset_mock()
    mocked_generation_service._generate_with_ollama.reset_mock()
    
    # Test avec Ollama
    await mocked_generation_service.generate_content(
        prompt=TEST_PROMPT,
        options=GenerationOptions(generation_type=GenerationType.OLLAMA)
    )
    mocked_generation_service._generate_with_ollama.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling_invalid_provider(mocked_generation_service):
    """Teste la gestion des erreurs lorsqu'un fournisseur invalide est spécifié."""
    # Modifie la classe pour simuler un fournisseur manquant
    original_methods = {}
    for method in ["_generate_with_openai", "_generate_with_anthropic", 
                   "_generate_with_gemini", "_generate_with_ollama"]:
        original_methods[method] = getattr(mocked_generation_service, method)
        setattr(mocked_generation_service, method, None)
    
    # Teste avec un fournisseur qui n'est plus disponible
    with pytest.raises(ValueError, match="non disponible"):
        await mocked_generation_service.generate_content(
            prompt=TEST_PROMPT,
            options=GenerationOptions(generation_type=GenerationType.OPENAI)
        )
    
    # Restaure les méthodes originales
    for method, original in original_methods.items():
        setattr(mocked_generation_service, method, original)
