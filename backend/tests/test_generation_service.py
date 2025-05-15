# backend/tests/test_generation_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.generation.service import GenerationService
from app.generation.models import (
    ContentType,
    ContentTone,
    GenerationParameters,
    GeneratedContent
)

# Test fixtures
@pytest.fixture
def generation_service_mock():
    """Create a GenerationService instance with mocked clients."""
    with patch("openai.OpenAI"), patch("anthropic.Anthropic"):
        service = GenerationService()
        service.openai_client = MagicMock()
        service.anthropic_client = MagicMock()
        service.openai_api_key = "fake-api-key"
        service.anthropic_api_key = "fake-api-key"
        return service

@pytest.fixture
def generation_parameters():
    """Create sample generation parameters for testing."""
    return GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Test post about AI technology",
        keywords=["AI", "technology", "innovation"],
        tone=ContentTone.PROFESSIONAL,
        max_length=400,
        language="fr",
        include_hashtags=True,
        include_emojis=True
    )

# Helper function to mock the OpenAI response
def mock_openai_response():
    chat_completion = MagicMock()
    chat_completion.choices = [MagicMock()]
    chat_completion.choices[0].message = MagicMock()
    chat_completion.choices[0].message.content = """
    {
        "content": "Aujourd'hui, nous sommes ravis de vous présenter notre dernière innovation en matière d'IA ! 🚀\\n\\nNotre équipe a développé une technologie révolutionnaire qui transforme la manière dont les entreprises abordent l'automatisation des processus. Cette solution combine l'apprentissage profond et le traitement du langage naturel pour offrir des résultats inégalés.\\n\\n💡 Principales caractéristiques:\\n• Analyse prédictive avancée\\n• Traitement en temps réel\\n• Intégration simplifiée avec vos systèmes existants\\n\\nNous recherchons actuellement des partenaires pour notre programme bêta. Intéressé(e) ? Contactez-nous en message privé !",
        "variants": ["Variante 1", "Variante 2"],
        "hashtags": ["#IntelligenceArtificielle", "#Innovation", "#Technologie", "#IA", "#TransformationDigitale"],
        "title": null,
        "summary": "Annonce de notre nouvelle solution d'IA générative"
    }
    """
    return chat_completion

# Helper function to mock the Anthropic response
def mock_anthropic_response():
    response = MagicMock()
    response.content = [MagicMock()]
    response.content[0].text = """
    {
        "content": "Notre équipe est fière d'annoncer une percée majeure dans le domaine de l'IA ! 🚀\\n\\nAprès des mois de recherche et développement intensifs, nous avons créé une solution technologique qui redéfinit les standards de l'industrie. Cette innovation permet d'automatiser des processus complexes tout en maintenant une précision exceptionnelle.\\n\\n✨ Avantages clés :\\n• Réduction des coûts opérationnels de 40%\\n• Amélioration de la précision de 85%\\n• Déploiement rapide et sans friction\\n\\nVous souhaitez découvrir comment cette technologie peut transformer votre entreprise ? Prenons rendez-vous !",
        "variants": ["Variante A", "Variante B"],
        "hashtags": ["#TechInnovation", "#IA", "#TransformationDigitale", "#FuturDuTravail"],
        "title": null,
        "summary": "Présentation de notre solution d'IA révolutionnaire"
    }
    """
    return response

# Tests for GenerationService
@pytest.mark.asyncio
async def test_generate_content_with_openai(generation_service_mock, generation_parameters):
    """Test generating content using the OpenAI client."""
    # Mock the OpenAI client's response
    openai_response = mock_openai_response()
    generation_service_mock.openai_client.chat.completions.create = AsyncMock(return_value=openai_response)
    
    # Call the generate_content method
    result = await generation_service_mock.generate_content(generation_parameters)
    
    # Assertions
    assert isinstance(result, GeneratedContent)
    assert result.content_type == ContentType.LINKEDIN_POST
    assert "#IntelligenceArtificielle" in result.content or "#Innovation" in result.content
    assert "🚀" in result.content  # Check for emoji
    assert result.parameters == generation_parameters
    
    # Verify method was called with expected parameters
    generation_service_mock.openai_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_content_with_anthropic(generation_service_mock, generation_parameters):
    """Test generating content using the Anthropic client when OpenAI fails."""
    # Mock OpenAI to raise an exception and force fallback to Anthropic
    generation_service_mock.openai_client.chat.completions.create = AsyncMock(side_effect=Exception("OpenAI API error"))
    
    # Mock the Anthropic client's response
    anthropic_response = mock_anthropic_response()
    generation_service_mock.anthropic_client.messages.create = AsyncMock(return_value=anthropic_response)
    
    # Call the generate_content method
    result = await generation_service_mock.generate_content(generation_parameters)
    
    # Assertions
    assert isinstance(result, GeneratedContent)
    assert result.content_type == ContentType.LINKEDIN_POST
    assert "#TechInnovation" in result.content or "#IA" in result.content
    assert "🚀" in result.content  # Check for emoji
    assert result.parameters == generation_parameters
    
    # Verify methods were called
    generation_service_mock.openai_client.chat.completions.create.assert_called_once()
    generation_service_mock.anthropic_client.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_content_fallback_to_template(generation_service, generation_parameters):
    """Test generating content with template fallback when both API clients fail."""
    # Mock both clients to fail
    generation_service.openai_client.chat.completions.create = AsyncMock(side_effect=Exception("OpenAI API error"))
    generation_service.anthropic_client.messages.create = AsyncMock(side_effect=Exception("Anthropic API error"))
    
    # Call the generate_content method
    result = await generation_service.generate_content(generation_parameters)
    
    # Assertions
    assert isinstance(result, GeneratedContent)
    assert result.content_type == ContentType.LINKEDIN_POST
    assert "AI" in result.content or "technology" in result.content
    assert result.parameters == generation_parameters
    
    # Verify both clients were attempted
    generation_service.openai_client.chat.completions.create.assert_called_once()
    generation_service.anthropic_client.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_content_by_id(generation_service_mock, generation_parameters):
    """Test retrieving generated content by ID."""
    # First generate some content
    openai_response = mock_openai_response()
    generation_service_mock.openai_client.chat.completions.create = AsyncMock(return_value=openai_response)
    
    generated = await generation_service_mock.generate_content(generation_parameters)
    content_id = generated.content_id
    
    # Now retrieve it
    retrieved = await generation_service_mock.get_content_by_id(content_id)
    
    # Assertions
    assert retrieved is not None
    assert retrieved.content_id == content_id
    assert retrieved.content == generated.content
    assert retrieved.content_type == ContentType.LINKEDIN_POST

@pytest.mark.asyncio
async def test_get_content_by_id_not_found(generation_service_mock):
    """Test retrieving content with an ID that doesn't exist."""
    non_existent_id = "non-existent-id"
    
    result = await generation_service_mock.get_content_by_id(non_existent_id)
    
    assert result is None

@pytest.mark.asyncio
async def test_generate_content_with_variants(generation_service, generation_parameters):
    """Test generating content with variants."""
    # Update parameters to request variants
    generation_parameters.additional_context = {"generate_variants": True, "variant_count": 2}
    
    # Mock OpenAI to return different content for each call
    openai_responses = [mock_openai_response() for _ in range(3)]  # 1 main + 2 variants
    generation_service.openai_client.chat.completions.create = AsyncMock(side_effect=openai_responses)
    
    # Call the generate_content method
    result = await generation_service.generate_content(generation_parameters)
    
    # Assertions
    assert isinstance(result, GeneratedContent)
    assert result.variants is not None
    assert len(result.variants) == 2  # Requested 2 variants

@pytest.mark.asyncio
async def test_validate_parameters(generation_service):
    """Test parameter validation for content generation."""
    # Test with invalid content type
    with pytest.raises(ValueError):
        params = GenerationParameters(
            content_type="invalid_type",  # type: ignore
            prompt="Test prompt"
        )
        await generation_service.generate_content(params)
    
    # Test with empty prompt
    with pytest.raises(ValueError):
        params = GenerationParameters(
            content_type=ContentType.LINKEDIN_POST,
            prompt=""
        )
        await generation_service.generate_content(params)
    
    # Test with max_length too small
    with pytest.raises(ValueError):
        params = GenerationParameters(
            content_type=ContentType.LINKEDIN_POST,
            prompt="Test prompt",
            max_length=10  # Too small for meaningful content
        )
        await generation_service.generate_content(params)

@pytest.mark.asyncio
async def test_format_twitter_post(generation_service_mock, generation_parameters):
    """Test formatting for Twitter posts (character limit check)."""
    # Change content type to Twitter
    generation_parameters.content_type = ContentType.TWITTER_POST
    generation_parameters.max_length = 280  # Twitter character limit
    
    # Mock a very long response that needs truncation
    chat_completion = MagicMock()
    chat_completion.choices = [MagicMock()]
    chat_completion.choices[0].message = MagicMock()
    chat_completion.choices[0].message.content = """
    {
        "content": "x" * 500,
        "hashtags": ["#Test"],
        "variants": []
    }
    """
    
    generation_service_mock.openai_client.chat.completions.create = AsyncMock(return_value=chat_completion)
    
    # Call the generate_content method
    result = await generation_service_mock.generate_content(generation_parameters)
    
    # Assertions
    assert isinstance(result, GeneratedContent)
    assert len(result.content) <= 280  # Should be truncated to Twitter limit

@pytest.mark.asyncio
async def test_generate_blog_article(generation_service_mock):
    """Test generating a longer-form blog article."""
    # Create parameters for a blog article
    blog_params = GenerationParameters(
        content_type=ContentType.BLOG_ARTICLE,
        prompt="The impact of AI on healthcare",
        keywords=["AI", "healthcare", "medical innovation"],
        tone=ContentTone.INFORMATIVE,
        max_length=2000,
        language="fr"
    )
    
    # Mock a response that includes an article with sections
    blog_response = MagicMock()
    blog_response.choices = [MagicMock()]
    blog_response.choices[0].message = MagicMock()
    blog_response.choices[0].message.content = """
    {
        "content": "# L'impact de l'IA sur le secteur de la santé\\n\\n## Introduction\\n\\nL'intelligence artificielle révolutionne de nombreux secteurs, et la santé n'est pas en reste...\\n\\n## Les applications actuelles\\n\\nAujourd'hui, l'IA est déjà utilisée dans plusieurs domaines médicaux...\\n\\n## Les défis à relever\\n\\nMalgré ces avancées, plusieurs défis persistent...\\n\\n## L'avenir de l'IA en santé\\n\\nDans les prochaines années, nous pouvons nous attendre à...\\n\\n## Conclusion\\n\\nL'IA offre un potentiel immense pour améliorer les soins de santé...",
        "variants": [],
        "hashtags": ["#IA", "#Santé", "#Innovation", "#MédecineDuFutur"],
        "title": "L'impact de l'IA sur le secteur de la santé",
        "summary": "Une analyse des applications actuelles et futures de l'intelligence artificielle dans le domaine médical."
    }
    """
    
    generation_service_mock.openai_client.chat.completions.create = AsyncMock(return_value=blog_response)
    
    # Call the generate_content method
    result = await generation_service_mock.generate_content(blog_params)
    
    # Assertions
    assert isinstance(result, GeneratedContent)
    assert result.content_type == ContentType.BLOG_ARTICLE
    assert "# L'impact de l'IA sur le secteur de la santé" in result.content
    assert "## Introduction" in result.content
    assert "## Conclusion" in result.content
