# backend/tests/test_publication_service.py
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

from app.publication.service import PublicationService
from app.publication.models import (
    SocialMediaPlatform,
    PublicationRequest,
    PublicationStatus,
    PublicationResult,
    DirectPublicationRequest
)
from app.generation.models import (
    ContentType,
    GenerationParameters,
    GeneratedContent
)
from app.generation.service import generation_service

# Test fixtures
@pytest.fixture
def publication_service():
    """Create a PublicationService instance with mocked clients."""
    with patch("app.publication.service.generation_service"):
        service = PublicationService()
        # Mock the LinkedIn client
        service.linkedin_client = MagicMock()
        service.linkedin_api_key = "fake-api-key"
        
        # Mock the Twitter client
        service.twitter_client = MagicMock()
        service.twitter_api_key = "fake-api-key"
        
        # Mock the Facebook client
        service.facebook_client = MagicMock()
        service.facebook_api_key = "fake-api-key"
        
        return service

@pytest.fixture
def generated_content():
    """Create a sample generated content for testing."""
    return GeneratedContent(
        content_id="test-content-123",
        content_type=ContentType.LINKEDIN_POST,
        content="Ceci est un post LinkedIn de test sur l'IA et l'innovation technologique. #IA #Innovation",
        hashtags=["#IA", "#Innovation", "#Technologie"],
        title="Post de test",
        summary="Un résumé du post de test",
        parameters=GenerationParameters(
            content_type=ContentType.LINKEDIN_POST,
            prompt="Post test sur l'IA"
        ),
        created_at=datetime.now().isoformat()
    )

@pytest.fixture
def publication_request():
    """Create a sample publication request."""
    return PublicationRequest(
        content_id="test-content-123",
        platform=SocialMediaPlatform.LINKEDIN,
        schedule_time=None,
        additional_options={"visibility": "public"}
    )

@pytest.fixture
def direct_publication_request():
    """Create a sample direct publication request."""
    return DirectPublicationRequest(
        content="Ceci est un post LinkedIn direct pour tester l'API. #Test",
        platform=SocialMediaPlatform.LINKEDIN,
        title="Test Direct Publication"
    )

# Tests for PublicationService
@pytest.mark.asyncio
async def test_publish_content_linkedin(publication_service, publication_request, generated_content):
    """Test publishing content to LinkedIn."""
    # Mock generation_service.get_content_by_id to return our fixture
    publication_service._get_content_by_id = AsyncMock(return_value=generated_content)
    
    # Mock the LinkedIn client publish method
    publication_service._publish_to_linkedin = AsyncMock(return_value={
        "platform_post_id": "linkedin-post-123",
        "platform_post_url": "https://www.linkedin.com/posts/test-123"
    })
    
    # Call the publish_content method
    result = await publication_service.publish_content(publication_request)
    
    # Assertions
    assert isinstance(result, PublicationResult)
    assert result.content_id == publication_request.content_id
    assert result.platform == SocialMediaPlatform.LINKEDIN
    assert result.status == PublicationStatus.PUBLISHED
    assert result.platform_post_id == "linkedin-post-123"
    assert result.platform_post_url == "https://www.linkedin.com/posts/test-123"
    
    # Verify methods were called
    publication_service._get_content_by_id.assert_called_with(publication_request.content_id)
    publication_service._publish_to_linkedin.assert_called_once()

@pytest.mark.asyncio
async def test_publish_content_twitter(publication_service, publication_request, generated_content):
    """Test publishing content to Twitter."""
    # Change the platform to Twitter
    publication_request.platform = SocialMediaPlatform.TWITTER
    generated_content.content_type = ContentType.TWITTER_POST
    
    # Mock generation_service.get_content_by_id to return our fixture
    publication_service._get_content_by_id = AsyncMock(return_value=generated_content)
    
    # Mock the Twitter client publish method
    publication_service._publish_to_twitter = AsyncMock(return_value={
        "platform_post_id": "twitter-post-123",
        "platform_post_url": "https://twitter.com/username/status/123456"
    })
    
    # Call the publish_content method
    result = await publication_service.publish_content(publication_request)
    
    # Assertions
    assert isinstance(result, PublicationResult)
    assert result.platform == SocialMediaPlatform.TWITTER
    assert result.status == PublicationStatus.PUBLISHED
    assert result.platform_post_id == "twitter-post-123"
    assert result.platform_post_url == "https://twitter.com/username/status/123456"
    
    # Verify methods were called
    publication_service._get_content_by_id.assert_called_with(publication_request.content_id)
    publication_service._publish_to_twitter.assert_called_once()

@pytest.mark.asyncio
async def test_publish_content_not_found(publication_service, publication_request):
    """Test publishing content that doesn't exist."""
    # Mock generation_service.get_content_by_id to return None (not found)
    publication_service._get_content_by_id = AsyncMock(return_value=None)
    
    # Call the publish_content method
    result = await publication_service.publish_content(publication_request)
    
    # Assertions
    assert isinstance(result, PublicationResult)
    assert result.content_id == publication_request.content_id
    assert result.status == PublicationStatus.FAILED
    assert "Contenu non trouvé" in result.error_message
    
    # Verify methods were called
    publication_service._get_content_by_id.assert_called_with(publication_request.content_id)

@pytest.mark.asyncio
async def test_publish_content_api_error(publication_service, publication_request, generated_content):
    """Test handling API errors during publication."""
    # Mock generation_service.get_content_by_id to return our fixture
    publication_service._get_content_by_id = AsyncMock(return_value=generated_content)
    
    # Mock the LinkedIn client to raise an exception
    publication_service._publish_to_linkedin = AsyncMock(side_effect=Exception("API Error"))
    
    # Call the publish_content method
    result = await publication_service.publish_content(publication_request)
    
    # Assertions
    assert isinstance(result, PublicationResult)
    assert result.content_id == publication_request.content_id
    assert result.status == PublicationStatus.FAILED
    assert "API Error" in result.error_message
    
    # Verify methods were called
    publication_service._get_content_by_id.assert_called_with(publication_request.content_id)
    publication_service._publish_to_linkedin.assert_called_once()

@pytest.mark.asyncio
async def test_publish_direct_content(publication_service, direct_publication_request):
    """Test publishing content directly without pre-generation."""
    # Mock the LinkedIn client publish method
    publication_service._publish_to_linkedin = AsyncMock(return_value={
        "platform_post_id": "linkedin-direct-123",
        "platform_post_url": "https://www.linkedin.com/posts/direct-123"
    })
    
    # Call the publish_direct method
    result = await publication_service.publish_direct(direct_publication_request)
    
    # Assertions
    assert isinstance(result, PublicationResult)
    assert result.platform == SocialMediaPlatform.LINKEDIN
    assert result.status == PublicationStatus.PUBLISHED
    assert result.platform_post_id == "linkedin-direct-123"
    assert result.platform_post_url == "https://www.linkedin.com/posts/direct-123"
    
    # Verify method was called
    publication_service._publish_to_linkedin.assert_called_once()

@pytest.mark.asyncio
async def test_schedule_publication(publication_service, publication_request, generated_content):
    """Test scheduling a publication for later."""
    # Add a schedule time to the request
    future_time = (datetime.now() + timedelta(hours=24)).isoformat()
    publication_request.schedule_time = future_time
    
    # Mock generation_service.get_content_by_id to return our fixture
    publication_service._get_content_by_id = AsyncMock(return_value=generated_content)
    
    # Call the publish_content method
    result = await publication_service.publish_content(publication_request)
    
    # Assertions
    assert isinstance(result, PublicationResult)
    assert result.status == PublicationStatus.SCHEDULED
    assert result.publication_time is None  # Not published yet
    
    # Check that the scheduled publication is in the service's queue
    assert len(publication_service._scheduled_publications) == 1
    scheduled_item = next(iter(publication_service._scheduled_publications.values()))
    assert scheduled_item["request"].content_id == publication_request.content_id
    assert scheduled_item["request"].schedule_time == future_time

@pytest.mark.asyncio
async def test_get_publication_history(publication_service, publication_request, generated_content):
    """Test retrieving publication history."""
    # First publish some content to add to history
    publication_service._get_content_by_id = AsyncMock(return_value=generated_content)
    publication_service._publish_to_linkedin = AsyncMock(return_value={
        "platform_post_id": "linkedin-post-123",
        "platform_post_url": "https://www.linkedin.com/posts/test-123"
    })
    
    await publication_service.publish_content(publication_request)
    
    # Call the get_publication_history method
    history = await publication_service.get_publication_history()
    
    # Assertions
    assert isinstance(history, list)
    assert len(history) == 1
    assert history[0].content_id == publication_request.content_id
    assert history[0].platform == SocialMediaPlatform.LINKEDIN
    assert history[0].status == PublicationStatus.PUBLISHED

@pytest.mark.asyncio
async def test_get_publication_by_id(publication_service, publication_request, generated_content):
    """Test retrieving a publication by ID."""
    # First publish some content
    publication_service._get_content_by_id = AsyncMock(return_value=generated_content)
    publication_service._publish_to_linkedin = AsyncMock(return_value={
        "platform_post_id": "linkedin-post-123",
        "platform_post_url": "https://www.linkedin.com/posts/test-123"
    })
    
    result = await publication_service.publish_content(publication_request)
    pub_id = result.publication_id
    
    # Call the get_publication_by_id method
    retrieved = await publication_service.get_publication_by_id(pub_id)
    
    # Assertions
    assert retrieved is not None
    assert retrieved.publication_id == pub_id
    assert retrieved.content_id == publication_request.content_id
    assert retrieved.platform == SocialMediaPlatform.LINKEDIN

@pytest.mark.asyncio
async def test_get_publication_by_id_not_found(publication_service):
    """Test retrieving a publication with an ID that doesn't exist."""
    non_existent_id = "non-existent-id"
    
    result = await publication_service.get_publication_by_id(non_existent_id)
    
    assert result is None

@pytest.mark.asyncio
async def test_generate_and_publish(publication_service, generated_content):
    """Test generating and publishing content in a single step."""
    # Mock the generation service
    with patch("app.publication.service.generation_service.generate_content", 
               new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = generated_content
        
        # Mock the LinkedIn client publish method
        publication_service._publish_to_linkedin = AsyncMock(return_value={
            "platform_post_id": "linkedin-post-123",
            "platform_post_url": "https://www.linkedin.com/posts/test-123"
        })
        
        # Call the generate_and_publish method
        result = await publication_service.generate_and_publish(
            platform=SocialMediaPlatform.LINKEDIN,
            generation_params=GenerationParameters(
                content_type=ContentType.LINKEDIN_POST,
                prompt="Test post"
            )
        )
        
        # Assertions
        assert isinstance(result, dict)
        assert "generation_result" in result
        assert "publication_result" in result
        assert result["generation_result"].content_id == generated_content.content_id
        assert result["publication_result"].platform == SocialMediaPlatform.LINKEDIN
        assert result["publication_result"].status == PublicationStatus.PUBLISHED
        
        # Verify methods were called
        mock_generate.assert_called_once()
        publication_service._publish_to_linkedin.assert_called_once()
