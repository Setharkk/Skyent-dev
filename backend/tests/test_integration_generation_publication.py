# backend/tests/test_integration_generation_publication.py
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.generation.service import GenerationService
from app.generation.models import (
    ContentType,
    ContentTone,
    GenerationParameters,
    GeneratedContent
)
from app.moderation.service import ModerationService
from app.moderation.models import (
    ModerationType,
    ModerationResult
)
from app.publication.service import PublicationService
from app.publication.models import (
    SocialMediaPlatform,
    PublicationStatus,
    PublicationResult
)

# Test fixture for end-to-end workflow
@pytest.fixture
def services():
    """Create service instances with mocked clients for integration testing."""
    with patch("openai.OpenAI"), patch("anthropic.Anthropic"):
        # Create generation service with mocked clients
        gen_service = GenerationService()
        gen_service.openai_client = MagicMock()
        gen_service.anthropic_client = MagicMock()
        gen_service.openai_api_key = "fake-api-key"
        gen_service.anthropic_api_key = "fake-api-key"
        
        # Create moderation service with mocked providers
        mod_service = ModerationService()
        mod_service.providers = {
            ModerationType.OPENAI: MagicMock(),
            ModerationType.ANTHROPIC: MagicMock(),
            ModerationType.DETOXIFY: MagicMock(),
            ModerationType.COMBINED: MagicMock()
        }
        
        # Create publication service with mocked clients
        pub_service = PublicationService()
        pub_service.linkedin_client = MagicMock()
        pub_service.twitter_client = MagicMock()
        pub_service.facebook_client = MagicMock()
        pub_service.linkedin_api_key = "fake-api-key"
        pub_service.twitter_api_key = "fake-api-key"
        pub_service.facebook_api_key = "fake-api-key"
        
        return {
            "generation": gen_service,
            "moderation": mod_service,
            "publication": pub_service
        }

# Mock response helpers
def mock_openai_generation_response():
    """Create a mock OpenAI generation response."""
    chat_completion = MagicMock()
    chat_completion.choices = [MagicMock()]
    chat_completion.choices[0].message = MagicMock()
    chat_completion.choices[0].message.content = """
    Nous sommes ravis d'annoncer le lancement de notre nouvelle solution de #IA générative ! 🚀

    Cette technologie innovante va transformer la manière dont vous créez du contenu et interagissez avec vos données. Avec notre solution, vous pouvez générer des textes de haute qualité, analyser des documents complexes et automatiser des tâches qui prenaient auparavant des heures.

    Contactez-nous pour une démo gratuite !

    #IntelligenceArtificielle #Innovation #Technologie
    """
    return chat_completion

def mock_moderation_safe_response():
    """Create a mock moderation response for safe content."""
    return ModerationResult(
        flagged=False,
        categories={
            "hate": False,
            "harassment": False,
            "self_harm": False,
            "sexual": False,
            "violence": False,
            "profanity": False
        },
        category_scores={
            "hate": 0.01,
            "harassment": 0.01,
            "self_harm": 0.01,
            "sexual": 0.01,
            "violence": 0.01,
            "profanity": 0.01
        },
        provider="openai",
        content_type="text"
    )

def mock_moderation_unsafe_response():
    """Create a mock moderation response for unsafe content."""
    return ModerationResult(
        flagged=True,
        categories={
            "hate": False,
            "harassment": True,
            "self_harm": False,
            "sexual": False,
            "violence": False,
            "profanity": True
        },
        category_scores={
            "hate": 0.01,
            "harassment": 0.75,
            "self_harm": 0.01,
            "sexual": 0.01,
            "violence": 0.01,
            "profanity": 0.85
        },
        provider="openai",
        content_type="text"
    )

def mock_linkedin_publication_response():
    """Create a mock LinkedIn publication response."""
    return {
        "platform_post_id": "linkedin-post-123",
        "platform_post_url": "https://www.linkedin.com/posts/test-123"
    }

# Integration tests
@pytest.mark.asyncio
async def test_generate_moderate_publish_workflow_success(services):
    """Test the full workflow: generation -> moderation -> publication (successful case)."""
    # Mock the generation service
    services["generation"].openai_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_generation_response()
    )
    
    # Mock the moderation service to indicate safe content
    services["moderation"].providers[ModerationType.COMBINED].moderate_content = AsyncMock(
        return_value=mock_moderation_safe_response()
    )
    
    # Mock the publication service to simulate successful posting
    services["publication"]._publish_to_linkedin = AsyncMock(
        return_value=mock_linkedin_publication_response()
    )
    
    # Step 1: Generate content
    generation_params = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Annonce du lancement de notre solution d'IA générative",
        keywords=["IA", "Innovation", "Technologie"],
        tone=ContentTone.PROFESSIONAL,
        include_hashtags=True,
        include_emojis=True
    )
    
    content = await services["generation"].generate_content(generation_params)
    assert content is not None
    assert isinstance(content, GeneratedContent)
    
    # Step 2: Moderate the content
    moderation_result = await services["moderation"].moderate_content(
        content=content.content,
        moderation_type=ModerationType.COMBINED
    )
    assert moderation_result is not None
    assert isinstance(moderation_result, ModerationResult)
    assert moderation_result.flagged is False
    
    # Step 3: If content is safe, publish it
    if not moderation_result.flagged:
        # Store the content in the publication service's internal storage
        services["publication"]._get_content_by_id = AsyncMock(return_value=content)
        
        publication_request = {
            "content_id": content.content_id,
            "platform": SocialMediaPlatform.LINKEDIN
        }
        
        publication_result = await services["publication"].publish_content(publication_request)
        assert publication_result is not None
        assert isinstance(publication_result, PublicationResult)
        assert publication_result.status == PublicationStatus.PUBLISHED
        assert publication_result.platform_post_url == "https://www.linkedin.com/posts/test-123"
    else:
        pytest.fail("Content was incorrectly flagged as unsafe")

@pytest.mark.asyncio
async def test_generate_moderate_publish_workflow_unsafe_content(services):
    """Test the workflow where content is flagged as unsafe by moderation."""
    # Mock the generation service
    services["generation"].openai_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_generation_response()
    )
    
    # Mock the moderation service to indicate unsafe content
    services["moderation"].providers[ModerationType.COMBINED].moderate_content = AsyncMock(
        return_value=mock_moderation_unsafe_response()
    )
    
    # Step 1: Generate content
    generation_params = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Annonce du lancement de notre solution d'IA générative",
        keywords=["IA", "Innovation", "Technologie"],
        tone=ContentTone.PROFESSIONAL,
        include_hashtags=True,
        include_emojis=True
    )
    
    content = await services["generation"].generate_content(generation_params)
    assert content is not None
    
    # Step 2: Moderate the content
    moderation_result = await services["moderation"].moderate_content(
        content=content.content,
        moderation_type=ModerationType.COMBINED
    )
    assert moderation_result is not None
    assert moderation_result.flagged is True
    
    # Step 3: Content should not be published if it's unsafe
    if moderation_result.flagged:
        # Verify that we don't proceed with publication
        # We could add code here to handle unsafe content (e.g., logging, alerting, etc.)
        print("Content was flagged as unsafe and not published")
    else:
        # If we get here, it means the content wasn't properly flagged
        pytest.fail("Unsafe content was not flagged correctly")

@pytest.mark.asyncio
async def test_end_to_end_generate_and_publish(services):
    """Test the end-to-end generate_and_publish method with moderation."""
    # Mock the generation service
    services["generation"].generate_content = AsyncMock(return_value=GeneratedContent(
        content_id="test-content-456",
        content_type=ContentType.LINKEDIN_POST,
        content="Contenu de test généré pour LinkedIn #IA #Technologie",
        hashtags=["#IA", "#Technologie"],
        parameters=GenerationParameters(
            content_type=ContentType.LINKEDIN_POST,
            prompt="Test post"
        ),
        created_at=datetime.now().isoformat()
    ))
    
    # Mock the moderation service
    services["moderation"].moderate_content = AsyncMock(return_value=mock_moderation_safe_response())
    
    # Mock the publication service methods
    services["publication"]._publish_to_linkedin = AsyncMock(return_value=mock_linkedin_publication_response())
    
    # Replace references to the original services with our mocked ones
    with patch("app.publication.service.generation_service", services["generation"]), \
         patch("app.publication.service.moderation_service", services["moderation"]):
        
        # Call the generate_and_publish method
        result = await services["publication"].generate_and_publish(
            platform=SocialMediaPlatform.LINKEDIN,
            generation_params=GenerationParameters(
                content_type=ContentType.LINKEDIN_POST,
                prompt="Test integrated workflow",
                keywords=["Test", "Integration"],
                tone=ContentTone.PROFESSIONAL
            )
        )
        
        # Assertions
        assert "generation_result" in result
        assert "publication_result" in result
        assert "moderation_result" in result
        assert not result["moderation_result"].flagged
        assert result["publication_result"].status == PublicationStatus.PUBLISHED
        
        # Verify methods were called
        services["generation"].generate_content.assert_called_once()
        services["moderation"].moderate_content.assert_called_once()
        services["publication"]._publish_to_linkedin.assert_called_once()
