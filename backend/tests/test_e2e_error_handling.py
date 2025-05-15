# backend/tests/test_e2e_error_handling.py
import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any
import uuid

from app.main import app
from app.generation.models import ContentType, ContentTone
from app.moderation.models import ContentType as ModContentType, ModerationType
from app.publication.models import SocialMediaPlatform

client = TestClient(app)

class TestErrorHandling:
    """Tests des scénarios d'erreur pour valider la robustesse de l'API."""
    
    def test_generation_invalid_parameters(self):
        """Tester la validation des paramètres de génération invalides."""
        # Test avec un type de contenu inexistant
        response = client.post(
            "/generation/content",
            json={
                "content_type": "inexistant_type",
                "prompt": "Test prompt"
            }
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test avec un prompt vide
        response = client.post(
            "/generation/content",
            json={
                "content_type": ContentType.LINKEDIN_POST.value,
                "prompt": ""
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_nonexistent_content(self):
        """Tester la récupération d'un contenu inexistant."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/generation/content/{fake_id}")
        
        assert response.status_code == 404
        assert "non trouvé" in response.json()["detail"]
    
    def test_moderation_invalid_parameters(self):
        """Tester la validation des paramètres de modération invalides."""
        # Test avec un type de modération inexistant
        response = client.post(
            "/moderation/moderate",
            json={
                "content": "Test content",
                "content_type": ModContentType.TEXT.value,
                "moderation_type": "inexistant_type"
            }
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test avec un contenu vide
        response = client.post(
            "/moderation/moderate/text",
            params={
                "content": "",
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_nonexistent_publication(self):
        """Tester la récupération d'une publication inexistante."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/publication/publication/{fake_id}")
        
        assert response.status_code == 404
        assert "non trouvée" in response.json()["detail"]
    
    def test_publish_nonexistent_content(self):
        """Tester la publication d'un contenu inexistant."""
        fake_id = str(uuid.uuid4())
        response = client.post(
            "/publication/publish",
            json={
                "content_id": fake_id,
                "platform": SocialMediaPlatform.LINKEDIN.value
            }
        )
        
        assert response.status_code == 400  # Bad request or 404
        assert "non trouvé" in response.json()["detail"]
    
    def test_batch_moderation_empty_list(self):
        """Tester la modération par lots avec une liste vide."""
        response = client.post(
            "/moderation/moderate/batch",
            json=[],
            params={
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        # Devrait renvoyer une liste vide mais pas d'erreur
        assert response.status_code == 200
        assert response.json() == []
    
    def test_direct_publish_invalid_platform(self):
        """Tester la publication directe vers une plateforme invalide."""
        response = client.post(
            "/publication/direct",
            json={
                "content": "Test content",
                "platform": "inexistant_platform"
            }
        )
        
        assert response.status_code == 422  # Validation error
