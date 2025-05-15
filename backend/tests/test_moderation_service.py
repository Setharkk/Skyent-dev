# backend/tests/test_moderation_service.py
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.moderation.service import (
    ModerationService,
    OpenAIModerationProvider,
    AnthropicModerationProvider,
    DetoxifyModerationProvider,
    CombinedModerationProvider
)
from app.moderation.models import (
    ModerationResult,
    ContentType,
    ModerationType,
    ToxicityCategory
)

# Test fixtures
@pytest.fixture
def moderation_service():
    """Create a ModerationService instance with mocked providers."""
    service = ModerationService()
    # Mock the providers
    service.providers = {
        ModerationType.OPENAI: MagicMock(),
        ModerationType.ANTHROPIC: MagicMock(),
        ModerationType.DETOXIFY: MagicMock(),
        ModerationType.COMBINED: MagicMock()
    }
    return service

@pytest.fixture
def openai_provider():
    """Create a mocked OpenAIModerationProvider."""
    with patch("openai.OpenAI"):
        provider = OpenAIModerationProvider()
        provider.client = MagicMock()
        provider.api_key = "fake-api-key"
        return provider

@pytest.fixture
def anthropic_provider():
    """Create a mocked AnthropicModerationProvider."""
    with patch("anthropic.Anthropic"):
        provider = AnthropicModerationProvider()
        provider.client = MagicMock()
        provider.api_key = "fake-api-key"
        return provider

@pytest.fixture
def detoxify_provider():
    """Create a mocked DetoxifyModerationProvider."""
    with patch("detoxify.Detoxify"):
        provider = DetoxifyModerationProvider()
        provider._model_instance = MagicMock()
        return provider

@pytest.fixture
def combined_provider():
    """Create a mocked CombinedModerationProvider."""
    provider = CombinedModerationProvider()
    provider.providers = {
        "openai": MagicMock(),
        "anthropic": MagicMock(),
        "detoxify": MagicMock()
    }
    return provider

# Sample data
SAFE_TEXT = "Ceci est un texte normal qui ne devrait pas être signalé."
UNSAFE_TEXT = "Ceci est un texte contenant des insultes et des menaces qui mérite d'être signalé!"

# Helper functions to mock API responses
def mock_openai_moderation_response(is_flagged=False):
    """Create a mock OpenAI moderation response."""
    response = MagicMock()
    result = MagicMock()
    result.flagged = is_flagged
    
    # Mock the categories and scores
    categories = MagicMock()
    categories.model_dump.return_value = {
        "hate": is_flagged,
        "harassment": is_flagged,
        "self-harm": False,
        "sexual": False,
        "violence": False,
        "profanity": is_flagged
    }
    
    scores = MagicMock()
    scores.model_dump.return_value = {
        "hate": 0.8 if is_flagged else 0.01,
        "harassment": 0.7 if is_flagged else 0.02,
        "self-harm": 0.01,
        "sexual": 0.01,
        "violence": 0.02,
        "profanity": 0.9 if is_flagged else 0.03
    }
    
    result.categories = categories
    result.category_scores = scores
    
    response.results = [result]
    response.model_dump = MagicMock(return_value={"results": [{"flagged": is_flagged}]})
    
    # Mock moderation.create method to return this response
    moderation_create = MagicMock()
    moderation_create.create = MagicMock(return_value=response)
    
    return response

def mock_anthropic_moderation_response(is_flagged=False):
    """Create a mock Anthropic moderation response."""
    response = MagicMock()
    content = MagicMock()
    
    json_response = {
        "flagged": is_flagged,
        "categories": {
            "hate": is_flagged,
            "harassment": is_flagged,
            "self_harm": False,
            "sexual": False,
            "violence": False,
            "profanity": is_flagged
        },
        "category_scores": {
            "hate": 0.8 if is_flagged else 0.01,
            "harassment": 0.7 if is_flagged else 0.02,
            "self_harm": 0.01,
            "sexual": 0.01,
            "violence": 0.02,
            "profanity": 0.9 if is_flagged else 0.03
        },
        "explanation": "Ce contenu contient du harcèlement et des insultes" if is_flagged else "Ce contenu est sûr"
    }
    
    content.text = json.dumps(json_response)
    response.content = [content]
    response.model_dump = MagicMock(return_value={"content": [{"text": json.dumps(json_response)}]})
    
    return response

def mock_detoxify_prediction(is_flagged=False):
    """Create a mock Detoxify prediction."""
    return {
        "toxicity": 0.9 if is_flagged else 0.05,
        "severe_toxicity": 0.7 if is_flagged else 0.01,
        "obscene": 0.8 if is_flagged else 0.02,
        "threat": 0.3 if is_flagged else 0.01,
        "insult": 0.8 if is_flagged else 0.03,
        "identity_attack": 0.6 if is_flagged else 0.02,
        "sexual_explicit": 0.1 if is_flagged else 0.01
    }

# Tests for ModerationService
@pytest.mark.asyncio
async def test_moderate_content_openai_safe(openai_provider):
    """Test moderation of safe content with OpenAI provider."""
    # Mock the OpenAI client's response
    openai_response = mock_openai_moderation_response(is_flagged=False)
    openai_provider.client.moderations.create = MagicMock(return_value=openai_response)
    
    # Call the moderate_content method
    result = await openai_provider.moderate_content(SAFE_TEXT)
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is False
    assert result.provider == "openai"
    assert result.content_type == ContentType.TEXT
    
    # Verify client was called with expected parameters
    openai_provider.client.moderations.create.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_openai_unsafe(openai_provider):
    """Test moderation of unsafe content with OpenAI provider."""
    # Mock the OpenAI client's response
    openai_response = mock_openai_moderation_response(is_flagged=True)
    openai_provider.client.moderations.create = MagicMock(return_value=openai_response)
    
    # Call the moderate_content method
    result = await openai_provider.moderate_content(UNSAFE_TEXT)
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is True
    assert any(flagged for flagged in result.categories.values())
    assert result.provider == "openai"
    
    # Verify client was called
    openai_provider.client.moderations.create.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_anthropic_safe(anthropic_provider):
    """Test moderation of safe content with Anthropic provider."""
    # Mock the Anthropic client's response
    anthropic_response = mock_anthropic_moderation_response(is_flagged=False)
    anthropic_provider.client.messages.create = MagicMock(return_value=anthropic_response)
    
    # Call the moderate_content method
    result = await anthropic_provider.moderate_content(SAFE_TEXT)
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is False
    assert not any(result.categories.values())
    assert result.provider == "anthropic"
    
    # Verify client was called
    anthropic_provider.client.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_anthropic_unsafe(anthropic_provider):
    """Test moderation of unsafe content with Anthropic provider."""
    # Mock the Anthropic client's response
    anthropic_response = mock_anthropic_moderation_response(is_flagged=True)
    anthropic_provider.client.messages.create = MagicMock(return_value=anthropic_response)
    
    # Call the moderate_content method
    result = await anthropic_provider.moderate_content(UNSAFE_TEXT)
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is True
    assert any(flagged for flagged in result.categories.values())
    assert result.provider == "anthropic"
    
    # Verify client was called
    anthropic_provider.client.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_detoxify_safe(detoxify_provider):
    """Test moderation of safe content with Detoxify provider."""
    # Mock the Detoxify model's prediction
    detoxify_provider.model.predict = MagicMock(return_value=mock_detoxify_prediction(is_flagged=False))
    
    # Call the moderate_content method
    result = await detoxify_provider.moderate_content(SAFE_TEXT)
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is False
    assert not any(result.categories.values())
    assert result.provider == "detoxify"
    
    # Verify model was called
    detoxify_provider.model.predict.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_detoxify_unsafe(detoxify_provider):
    """Test moderation of unsafe content with Detoxify provider."""
    # Mock the Detoxify model's prediction
    detoxify_provider.model.predict = MagicMock(return_value=mock_detoxify_prediction(is_flagged=True))
    
    # Call the moderate_content method
    result = await detoxify_provider.moderate_content(UNSAFE_TEXT)
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is True
    assert any(flagged for flagged in result.categories.values())
    assert result.provider == "detoxify"
    
    # Verify model was called
    detoxify_provider.model.predict.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_combined_all_safe(combined_provider):
    """Test combined moderation where all providers flag content as safe."""
    # Mock each provider to return safe content
    for provider_name, provider in combined_provider.providers.items():
        provider.moderate_content = AsyncMock(return_value=ModerationResult(
            flagged=False,
            categories={
                ToxicityCategory.HATE: False,
                ToxicityCategory.HARASSMENT: False,
                ToxicityCategory.SELF_HARM: False,
                ToxicityCategory.SEXUAL: False,
                ToxicityCategory.VIOLENCE: False,
                ToxicityCategory.PROFANITY: False
            },
            category_scores={
                ToxicityCategory.HATE: 0.01,
                ToxicityCategory.HARASSMENT: 0.02,
                ToxicityCategory.SELF_HARM: 0.01,
                ToxicityCategory.SEXUAL: 0.01,
                ToxicityCategory.VIOLENCE: 0.01,
                ToxicityCategory.PROFANITY: 0.02
            },
            provider=provider_name,
            content_type=ContentType.TEXT
        ))
    
    # Call the moderate_content method directly
    result = await combined_provider.moderate_content(SAFE_TEXT, providers=list(combined_provider.providers.keys()))
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is False
    assert not any(result.categories.values())
    assert result.provider == "combined"
    
    # Verify providers were called
    for provider in combined_provider.providers.values():
        assert provider.moderate_content.called

@pytest.mark.asyncio
async def test_moderate_content_combined_one_flags(combined_provider):
    """Test combined moderation where at least one provider flags content."""
    # Mock each provider to return different results
    combined_provider.providers["openai"].moderate_content = AsyncMock(return_value=ModerationResult(
        flagged=False,  # OpenAI says safe
        categories={ToxicityCategory.HATE: False, ToxicityCategory.HARASSMENT: False},
        category_scores={ToxicityCategory.HATE: 0.01, ToxicityCategory.HARASSMENT: 0.02},
        provider="openai",
        content_type=ContentType.TEXT
    ))
    
    combined_provider.providers["anthropic"].moderate_content = AsyncMock(return_value=ModerationResult(
        flagged=True,  # Anthropic says unsafe
        categories={ToxicityCategory.HATE: True, ToxicityCategory.HARASSMENT: False},
        category_scores={ToxicityCategory.HATE: 0.78, ToxicityCategory.HARASSMENT: 0.02},
        provider="anthropic",
        content_type=ContentType.TEXT
    ))
    
    combined_provider.providers["detoxify"].moderate_content = AsyncMock(return_value=ModerationResult(
        flagged=False,  # Detoxify says safe
        categories={ToxicityCategory.HATE: False, ToxicityCategory.HARASSMENT: False},
        category_scores={ToxicityCategory.HATE: 0.45, ToxicityCategory.HARASSMENT: 0.02},
        provider="detoxify",
        content_type=ContentType.TEXT
    ))
    
    # Call the moderate_content method
    result = await combined_provider.moderate_content(UNSAFE_TEXT, providers=["openai", "anthropic", "detoxify"])
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.flagged is True  # Combined result should be flagged
    assert result.categories.get(ToxicityCategory.HATE) is True
    assert result.provider == "combined"
    
    # Verify the maximum score was taken
    assert result.category_scores.get(ToxicityCategory.HATE) == 0.78
    
    # Verify providers were called
    for provider in combined_provider.providers.values():
        provider.moderate_content.assert_called_once()

@pytest.mark.asyncio
async def test_moderation_service_selection(moderation_service):
    """Test that ModerationService selects the correct provider."""
    # Set up mock results for each provider
    safe_result = ModerationResult(
        flagged=False,
        categories={ToxicityCategory.HATE: False},
        category_scores={ToxicityCategory.HATE: 0.01},
        provider="test",
        content_type=ContentType.TEXT
    )
    
    unsafe_result = ModerationResult(
        flagged=True,
        categories={ToxicityCategory.HATE: True},
        category_scores={ToxicityCategory.HATE: 0.85},
        provider="test",
        content_type=ContentType.TEXT
    )
    
    # Set up provider mocks
    moderation_service.providers[ModerationType.OPENAI].moderate_content = AsyncMock(return_value=safe_result)
    moderation_service.providers[ModerationType.ANTHROPIC].moderate_content = AsyncMock(return_value=unsafe_result)
    moderation_service.providers[ModerationType.DETOXIFY].moderate_content = AsyncMock(return_value=safe_result)
    moderation_service.providers[ModerationType.COMBINED].moderate_content = AsyncMock(return_value=unsafe_result)
    
    # Test OpenAI provider selection
    result_openai = await moderation_service.moderate_content(
        "Test content",
        moderation_type=ModerationType.OPENAI
    )
    assert result_openai.flagged is False
    moderation_service.providers[ModerationType.OPENAI].moderate_content.assert_called_once()
    
    # Test Anthropic provider selection
    result_anthropic = await moderation_service.moderate_content(
        "Test content",
        moderation_type=ModerationType.ANTHROPIC
    )
    assert result_anthropic.flagged is True
    moderation_service.providers[ModerationType.ANTHROPIC].moderate_content.assert_called_once()
    
    # Test Combined provider selection (default)
    result_combined = await moderation_service.moderate_content(
        "Test content"  # ModerationType.COMBINED is the default
    )
    assert result_combined.flagged is True
    moderation_service.providers[ModerationType.COMBINED].moderate_content.assert_called_once()

@pytest.mark.asyncio
async def test_moderate_content_with_list_input(moderation_service):
    """Test moderation with a list of texts."""
    # Set up mock result
    safe_result = ModerationResult(
        flagged=False,
        categories={ToxicityCategory.HATE: False},
        category_scores={ToxicityCategory.HATE: 0.01},
        provider="test",
        content_type=ContentType.TEXT
    )
    
    # Set up provider mock
    moderation_service.providers[ModerationType.COMBINED].moderate_content = AsyncMock(return_value=safe_result)
    
    # Call with a list of texts
    texts = ["Text 1", "Text 2", "Text 3"]
    result = await moderation_service.moderate_content(texts)
    
    # Assertions
    assert result is safe_result
    # Vérifier uniquement que la fonction a été appelée avec le bon texte
    moderation_service.providers[ModerationType.COMBINED].moderate_content.assert_called_once()
    call_args = moderation_service.providers[ModerationType.COMBINED].moderate_content.call_args[0]
    assert call_args[0] == texts

@pytest.mark.asyncio
async def test_error_handling_invalid_provider(moderation_service):
    """Test error handling when an invalid provider is specified."""
    # Remove a provider to simulate it not being available
    del moderation_service.providers[ModerationType.OPENAI]
    
    # Try to use the removed provider
    with pytest.raises(ValueError, match="non supporté"):
        await moderation_service.moderate_content("Test content", moderation_type=ModerationType.OPENAI)

@pytest.mark.asyncio
async def test_provider_failure_handling(combined_provider):
    """Test handling when some providers fail."""
    # Make the OpenAI provider raise an exception
    combined_provider.providers["openai"].moderate_content = AsyncMock(side_effect=Exception("API Error"))
    
    # Make the other providers return normal results
    combined_provider.providers["anthropic"].moderate_content = AsyncMock(return_value=ModerationResult(
        flagged=False,
        categories={ToxicityCategory.HATE: False},
        category_scores={ToxicityCategory.HATE: 0.01},
        provider="anthropic",
        content_type=ContentType.TEXT
    ))
    
    combined_provider.providers["detoxify"].moderate_content = AsyncMock(return_value=ModerationResult(
        flagged=False,
        categories={ToxicityCategory.HARASSMENT: False},
        category_scores={ToxicityCategory.HARASSMENT: 0.02},
        provider="detoxify",
        content_type=ContentType.TEXT
    ))
    
    # Call the moderate_content method
    result = await combined_provider.moderate_content(
        SAFE_TEXT, 
        providers=["openai", "anthropic", "detoxify"]
    )
    
    # Assertions
    assert isinstance(result, ModerationResult)
    assert result.provider == "combined"
    
    # Should still have results from the other providers
    assert ToxicityCategory.HATE in result.categories
    assert ToxicityCategory.HARASSMENT in result.categories
