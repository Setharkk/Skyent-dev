# backend/app/moderation/test_moderation.py
import unittest
import asyncio
from unittest.mock import patch, MagicMock
import os

from .models import ModerationResult, ContentType, ModerationType, ToxicityCategory
from .service import (
    ModerationService, 
    OpenAIModerationProvider,
    AnthropicModerationProvider,
    DetoxifyModerationProvider,
    CombinedModerationProvider
)

class TestModeration(unittest.TestCase):
    """Tests unitaires pour le module de modération."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        # Sauvegarder les variables d'environnement existantes
        self.original_openai_key = os.environ.get("OPENAI_API_KEY")
        self.original_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # Définir des clés API fictives pour les tests
        os.environ["OPENAI_API_KEY"] = "test_openai_key"
        os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
        
        # Créer le service de modération
        self.service = ModerationService()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Restaurer les variables d'environnement
        if self.original_openai_key:
            os.environ["OPENAI_API_KEY"] = self.original_openai_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)
            
        if self.original_anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = self.original_anthropic_key
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)
    
    @patch("openai.OpenAI")
    def test_openai_moderation(self, mock_openai):
        """Test de la modération via OpenAI."""
        # Configuration du mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_moderation_response = MagicMock()
        mock_result = MagicMock()
        mock_result.flagged = True
        mock_result.categories = MagicMock()
        mock_result.categories.model_dump.return_value = {
            "sexual": True,
            "hate": False,
            "harassment": False,
            "self-harm": False,
            "violence": False
        }
        mock_result.category_scores = MagicMock()
        mock_result.category_scores.model_dump.return_value = {
            "sexual": 0.8,
            "hate": 0.1,
            "harassment": 0.2,
            "self-harm": 0.0,
            "violence": 0.3
        }
        mock_moderation_response.results = [mock_result]
        mock_moderation_response.model_dump.return_value = {"test": "response"}
        mock_client.moderations.create.return_value = mock_moderation_response
        
        # Créer un fournisseur OpenAI avec le mock
        provider = OpenAIModerationProvider()
        provider.client = mock_client
        
        # Exécuter la modération
        result = asyncio.run(provider.moderate_content("test content", include_original_response=True))
        
        # Vérifier les appels et le résultat
        mock_client.moderations.create.assert_called_once_with(input=["test content"])
        self.assertTrue(result.flagged)
        self.assertTrue(result.categories[ToxicityCategory.SEXUAL])
        self.assertFalse(result.categories[ToxicityCategory.HATE])
        self.assertEqual(result.category_scores[ToxicityCategory.SEXUAL], 0.8)
        self.assertEqual(result.provider, "openai")
    
    @patch("anthropic.Anthropic")
    def test_anthropic_moderation(self, mock_anthropic):
        """Test de la modération via Anthropic."""
        # Configuration du mock
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """
        {
            "flagged": true,
            "categories": {
                "hate": false,
                "harassment": true,
                "self_harm": false,
                "sexual": false,
                "violence": false,
                "profanity": true
            },
            "category_scores": {
                "hate": 0.1,
                "harassment": 0.7,
                "self_harm": 0.0,
                "sexual": 0.2,
                "violence": 0.3,
                "profanity": 0.8
            },
            "explanation": "Le contenu contient du harcèlement et des grossièretés"
        }
        """
        mock_message.content = [mock_content]
        mock_message.model_dump.return_value = {"test": "response"}
        mock_client.messages.create.return_value = mock_message
        
        # Créer un fournisseur Anthropic avec le mock
        provider = AnthropicModerationProvider()
        provider.client = mock_client
        
        # Exécuter la modération
        result = asyncio.run(provider.moderate_content("test content", include_original_response=True))
        
        # Vérifier les appels et le résultat
        self.assertTrue(mock_client.messages.create.called)
        self.assertTrue(result.flagged)
        self.assertFalse(result.categories[ToxicityCategory.HATE])
        self.assertTrue(result.categories[ToxicityCategory.HARASSMENT])
        self.assertTrue(result.categories[ToxicityCategory.PROFANITY])
        self.assertEqual(result.category_scores[ToxicityCategory.HARASSMENT], 0.7)
        self.assertEqual(result.provider, "anthropic")
    
    @patch("detoxify.Detoxify")
    def test_detoxify_moderation(self, mock_detoxify):
        """Test de la modération via Detoxify."""
        # Configuration du mock
        mock_model = MagicMock()
        mock_detoxify.return_value = mock_model
        
        # Résultats simulés de Detoxify
        mock_model.predict.return_value = {
            "toxicity": 0.9,
            "severe_toxicity": 0.5,
            "obscene": 0.8,
            "threat": 0.1,
            "insult": 0.7,
            "identity_attack": 0.3,
            "sexual_explicit": 0.2
        }
        
        # Créer un fournisseur Detoxify avec le mock
        provider = DetoxifyModerationProvider()
        # Remplacer la propriété model par notre mock
        type(provider).model = mock_model
        
        # Exécuter la modération
        result = asyncio.run(provider.moderate_content("test content", include_original_response=True))
        
        # Vérifier les appels et le résultat
        mock_model.predict.assert_called_once_with("test content")
        self.assertTrue(result.flagged)
        self.assertTrue(result.categories[ToxicityCategory.OTHER])  # "toxicity" est mappé à "OTHER"
        self.assertTrue(result.categories[ToxicityCategory.PROFANITY])  # "obscene" est mappé à "PROFANITY"
        self.assertEqual(result.category_scores[ToxicityCategory.HARASSMENT], 0.7)  # "insult" est mappé à "HARASSMENT"
        self.assertEqual(result.provider, "detoxify")
    
    @patch.object(OpenAIModerationProvider, "moderate_content")
    @patch.object(DetoxifyModerationProvider, "moderate_content")
    def test_combined_moderation(self, mock_detoxify_moderate, mock_openai_moderate):
        """Test de la modération combinée."""
        # Configuration des mocks pour les résultats des fournisseurs
        openai_result = ModerationResult(
            flagged=True,
            categories={
                ToxicityCategory.HATE: True,
                ToxicityCategory.SEXUAL: False
            },
            category_scores={
                ToxicityCategory.HATE: 0.8,
                ToxicityCategory.SEXUAL: 0.3
            },
            provider="openai",
            content_type=ContentType.TEXT
        )
        
        detoxify_result = ModerationResult(
            flagged=True,
            categories={
                ToxicityCategory.HATE: False,
                ToxicityCategory.SEXUAL: True
            },
            category_scores={
                ToxicityCategory.HATE: 0.4,
                ToxicityCategory.SEXUAL: 0.9
            },
            provider="detoxify",
            content_type=ContentType.TEXT
        )
        
        # Configurer les mocks pour retourner ces résultats
        mock_openai_moderate.return_value = openai_result
        mock_detoxify_moderate.return_value = detoxify_result
        
        # Créer un fournisseur combiné
        provider = CombinedModerationProvider()
        
        # Assurer que les fournisseurs internes ont des clients initialisés
        for p in provider.providers.values():
            if hasattr(p, "client"):
                p.client = MagicMock()
        
        # Exécuter la modération
        result = asyncio.run(provider.moderate_content(
            "test content", 
            providers=["openai", "detoxify"],
            include_original_response=True
        ))
        
        # Vérifier le résultat combiné
        self.assertTrue(result.flagged)
        self.assertTrue(result.categories[ToxicityCategory.HATE])
        self.assertTrue(result.categories[ToxicityCategory.SEXUAL])
        self.assertEqual(result.category_scores[ToxicityCategory.HATE], 0.8)  # Prend le max des deux scores
        self.assertEqual(result.category_scores[ToxicityCategory.SEXUAL], 0.9)  # Prend le max des deux scores
        self.assertEqual(result.provider, "combined")
    
    def test_moderation_service(self):
        """Test du service de modération principal."""
        # Patcher les méthodes de modération des fournisseurs
        with patch.object(OpenAIModerationProvider, "moderate_content") as mock_openai, \
             patch.object(DetoxifyModerationProvider, "moderate_content") as mock_detoxify, \
             patch.object(AnthropicModerationProvider, "moderate_content") as mock_anthropic, \
             patch.object(CombinedModerationProvider, "moderate_content") as mock_combined:
            
            # Configurer des résultats simulés
            mock_result = ModerationResult(
                flagged=True,
                categories={ToxicityCategory.HATE: True},
                category_scores={ToxicityCategory.HATE: 0.8},
                provider="test",
                content_type=ContentType.TEXT
            )
            
            mock_openai.return_value = mock_result
            mock_detoxify.return_value = mock_result
            mock_anthropic.return_value = mock_result
            mock_combined.return_value = mock_result
            
            # Tester chaque type de modération
            for moderation_type in ModerationType:
                result = asyncio.run(self.service.moderate_content(
                    "test content",
                    moderation_type=moderation_type
                ))
                
                # Vérifier que le résultat est correct
                self.assertEqual(result, mock_result)


if __name__ == "__main__":
    unittest.main()
