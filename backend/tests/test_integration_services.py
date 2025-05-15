# backend/tests/test_integration_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime

from app.generation.service import GenerationService
from app.generation.models import ContentType, ContentTone, GenerationParameters, GeneratedContent
from app.moderation.service import ModerationService, ModerationType
from app.moderation.models import ModerationResult, ToxicityCategory, ContentType as ModerationContentType
from app.publication.service import PublicationService
from app.publication.models import PublicationResult, PublicationStatus, SocialMediaPlatform, DirectPublicationRequest

# Exemple de données d'entrée
TEST_PROMPT = "Générer un post sur les avantages du développement durable"
TEST_CONTENT = "Le développement durable offre de nombreux avantages pour notre planète et les générations futures."
TEST_UNSAFE_CONTENT = "Contenu inapproprié qui devrait être détecté par la modération."

@pytest.fixture
def mock_generation_service():
    """Create a mocked GenerationService."""
    service = MagicMock(spec=GenerationService)
    service.generate_content = AsyncMock()
    service.generate_content.return_value = GeneratedContent(
        content_id="test-content-id",
        content_type=ContentType.LINKEDIN_POST,
        content=TEST_CONTENT,
        variants=None,
        hashtags=["#développementdurable", "#environnement"],
        title=None,
        summary=None,
        parameters=GenerationParameters(
            prompt=TEST_PROMPT,
            content_type=ContentType.LINKEDIN_POST,
            tone=ContentTone.PROFESSIONAL
        ),
        created_at=datetime.now().isoformat(),
        metadata=None
    )
    return service

@pytest.fixture
def mock_moderation_service():
    """Create a mocked ModerationService."""
    service = MagicMock(spec=ModerationService)
    service.moderate_content = AsyncMock()
    
    # Par défaut, retourne un contenu sûr
    service.moderate_content.return_value = ModerationResult(
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
            ToxicityCategory.HARASSMENT: 0.01,
            ToxicityCategory.SELF_HARM: 0.01,
            ToxicityCategory.SEXUAL: 0.01,
            ToxicityCategory.VIOLENCE: 0.01,
            ToxicityCategory.PROFANITY: 0.01
        },
        provider="combined",
        content_type=ModerationContentType.TEXT
    )
    return service

@pytest.fixture
def mock_publication_service():
    """Create a mocked PublicationService."""
    service = MagicMock(spec=PublicationService)
    service.direct_publish = AsyncMock()
    service.direct_publish.return_value = PublicationResult(
        publication_id="test-publication-id",
        content_id="test-content-id",
        platform=SocialMediaPlatform.LINKEDIN,
        platform_post_url="https://linkedin.com/post/12345",
        platform_post_id="12345",
        status=PublicationStatus.PUBLISHED,
        publication_time=datetime.now().isoformat(),
        error_message=None
    )
    return service

@pytest.mark.asyncio
async def test_full_generation_moderation_publication_flow(
    mock_generation_service, mock_moderation_service, mock_publication_service):
    """Test the complete flow: Generation -> Moderation -> Publication."""
    
    # 1. Génération de contenu
    parameters = GenerationParameters(
        prompt=TEST_PROMPT,
        content_type=ContentType.LINKEDIN_POST,
        tone=ContentTone.PROFESSIONAL
    )
    
    generation_result = await mock_generation_service.generate_content(parameters)
    
    # 2. Modération du contenu généré
    moderation_result = await mock_moderation_service.moderate_content(
        generation_result.content,
        moderation_type=ModerationType.COMBINED
    )
    
    # Vérification que le contenu est approprié
    assert moderation_result.flagged is False, "Le contenu généré a été signalé comme inapproprié"
    
    # 3. Publication du contenu si approprié
    if not moderation_result.flagged:
        publication_request = DirectPublicationRequest(
            content=generation_result.content,
            platform=SocialMediaPlatform.LINKEDIN,
            additional_options={"audience": "professionals"}
        )
        
        publication_result = await mock_publication_service.direct_publish(publication_request)
        
        # Vérification de la publication
        assert publication_result.status == PublicationStatus.PUBLISHED
        assert publication_result.platform_post_id is not None
        assert publication_result.platform_post_url is not None

@pytest.mark.asyncio
async def test_moderation_blocking_inappropriate_content(
    mock_generation_service, mock_moderation_service, mock_publication_service):
    """Test que la modération bloque la publication de contenu inapproprié."""
    
    # 1. Configuration du mock pour générer du contenu inapproprié
    mock_generation_service.generate_content.return_value = GeneratedContent(
        content_id="test-unsafe-content-id",
        content_type=ContentType.LINKEDIN_POST,
        content=TEST_UNSAFE_CONTENT,
        variants=None,
        hashtags=["#test"],
        title=None,
        summary=None,
        parameters=GenerationParameters(
            prompt="Générer un post controversé",
            content_type=ContentType.LINKEDIN_POST,
            tone=ContentTone.SERIOUS
        ),
        created_at=datetime.now().isoformat(),
        metadata=None
    )
    
    # 2. Configuration du mock pour signaler le contenu comme inapproprié
    mock_moderation_service.moderate_content.return_value = ModerationResult(
        flagged=True,
        categories={
            ToxicityCategory.HATE: True,
            ToxicityCategory.HARASSMENT: False,
            ToxicityCategory.SELF_HARM: False,
            ToxicityCategory.SEXUAL: False,
            ToxicityCategory.VIOLENCE: False,
            ToxicityCategory.PROFANITY: False
        },
        category_scores={
            ToxicityCategory.HATE: 0.85,
            ToxicityCategory.HARASSMENT: 0.01,
            ToxicityCategory.SELF_HARM: 0.01,
            ToxicityCategory.SEXUAL: 0.01,
            ToxicityCategory.VIOLENCE: 0.01,
            ToxicityCategory.PROFANITY: 0.01
        },
        provider="combined",
        content_type=ModerationContentType.TEXT
    )
    
    # 3. Génération de contenu
    parameters = GenerationParameters(
        prompt="Générer un post controversé",
        content_type=ContentType.LINKEDIN_POST,
        tone=ContentTone.SERIOUS
    )
    
    generation_result = await mock_generation_service.generate_content(parameters)
    
    # 4. Modération du contenu généré
    moderation_result = await mock_moderation_service.moderate_content(
        generation_result.content,
        moderation_type=ModerationType.COMBINED
    )
    
    # 5. Vérification que le contenu est identifié comme inapproprié
    assert moderation_result.flagged is True
    assert moderation_result.categories.get(ToxicityCategory.HATE) is True
    
    # 6. Le contenu ne devrait pas être publié
    # Vérification que le service de publication n'a pas été appelé
    mock_publication_service.direct_publish.assert_not_called()
