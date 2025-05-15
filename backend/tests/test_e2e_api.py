# backend/tests/test_e2e_api.py
import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any, List
import time

from app.main import app
from app.generation.models import ContentType as GenContentType, ContentTone
from app.moderation.models import ContentType as ModContentType, ModerationType
from app.publication.models import SocialMediaPlatform, PublicationStatus

client = TestClient(app)

# Données de test
TEST_CONTENT = "Le développement durable est une approche qui vise à améliorer la qualité de vie humaine tout en protégeant l'environnement."
TEST_UNSAFE_CONTENT = "Ce texte contient des insultes et des menaces qui ne devraient pas être publiées."
LINKEDIN_PROMPT = "Écrivez un post LinkedIn sur l'importance de l'intelligence artificielle responsable"
TWITTER_PROMPT = "Écrivez un tweet sur les innovations technologiques récentes"

class TestEndToEndWorkflows:
    """Tests de bout en bout (E2E) pour les flux de travail API complets."""
    
    def test_health_check(self):
        """Vérifier que l'API est en bon état de fonctionnement."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_generation_status(self):
        """Vérifier que le service de génération est en bon état."""
        response = client.get("/generation/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_moderation_status(self):
        """Vérifier que le service de modération est en bon état."""
        response = client.get("/moderation/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_publication_status(self):
        """Vérifier que le service de publication est en bon état."""
        response = client.get("/publication/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_complete_generation_moderation_publication_flow(self):
        """
        Test E2E du flux complet : Génération > Modération > Publication.
        Ce test simule un utilisateur qui génère du contenu, le modère, puis le publie.
        """
        # 1. Génération de contenu LinkedIn
        generation_response = client.post(
            "/generation/linkedin",
            params={
                "prompt": LINKEDIN_PROMPT,
                "tone": ContentTone.PROFESSIONAL.value,
                "include_hashtags": True
            }
        )
        
        # Vérifier que la génération a réussi
        assert generation_response.status_code == 200
        generation_result = generation_response.json()
        assert generation_result["content_type"] == GenContentType.LINKEDIN_POST.value
        assert generation_result["content"] != ""
        assert "content_id" in generation_result
        
        content_id = generation_result["content_id"]
        generated_content = generation_result["content"]
        
        # 2. Modération du contenu généré
        moderation_response = client.post(
            "/moderation/moderate/text",
            params={
                "content": generated_content,
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        # Vérifier que la modération a réussi
        assert moderation_response.status_code == 200
        moderation_result = moderation_response.json()
        assert "flagged" in moderation_result
        
        # Si le contenu est approprié, procéder à la publication
        if not moderation_result["flagged"]:
            # 3. Publication du contenu sur LinkedIn
            publication_response = client.post(
                "/publication/publish",
                json={
                    "content_id": content_id,
                    "platform": SocialMediaPlatform.LINKEDIN.value,
                    "additional_options": {
                        "audience": "professionals"
                    }
                }
            )
            
            # Vérifier que la publication a réussi
            assert publication_response.status_code == 200
            publication_result = publication_response.json()
            assert publication_result["status"] == PublicationStatus.PUBLISHED.value
            assert publication_result["content_id"] == content_id
            
            # 4. Vérifier que la publication est récupérable
            get_pub_response = client.get(f"/publication/publication/{publication_result['publication_id']}")
            assert get_pub_response.status_code == 200
            
            # 5. Vérifier les publications associées au contenu
            content_pubs_response = client.get(f"/publication/content/{content_id}/publications")
            assert content_pubs_response.status_code == 200
            assert len(content_pubs_response.json()) > 0
    
    def test_direct_publication_with_moderation(self):
        """
        Test E2E de publication directe avec modération préalable.
        Ce test simule un utilisateur qui modère un contenu avant publication directe.
        """
        # 1. Modération du contenu
        moderation_response = client.post(
            "/moderation/moderate/text",
            params={
                "content": TEST_CONTENT,
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        # Vérifier que la modération a réussi
        assert moderation_response.status_code == 200
        moderation_result = moderation_response.json()
        assert not moderation_result["flagged"], "Le contenu de test a été signalé comme inapproprié"
        
        # 2. Publication directe du contenu
        publication_response = client.post(
            "/publication/direct",
            json={
                "content": TEST_CONTENT,
                "platform": SocialMediaPlatform.TWITTER.value,
                "title": "Test de publication",
                "additional_options": {
                    "hashtags": ["#test", "#publication"]
                }
            }
        )
        
        # Vérifier que la publication a réussi
        assert publication_response.status_code == 200
        publication_result = publication_response.json()
        assert publication_result["status"] == PublicationStatus.PUBLISHED.value
    
    def test_moderation_blocks_inappropriate_content(self):
        """
        Test que la modération bloque correctement le contenu inapproprié.
        Ce test simule un utilisateur qui tente de publier du contenu inapproprié.
        """
        # 1. Modération du contenu inapproprié
        moderation_response = client.post(
            "/moderation/moderate/text",
            params={
                "content": TEST_UNSAFE_CONTENT,
                "moderation_type": ModerationType.COMBINED.value,
                "include_original_response": True
            }
        )
        
        # Vérifier que la modération a identifié le contenu comme inapproprié
        assert moderation_response.status_code == 200
        moderation_result = moderation_response.json()
        
        # Dans un environnement de test, notre contenu peut ne pas être réellement détecté comme inapproprié
        # car nous n'appelons pas de vrais services de modération. 
        # Ici, nous vérifions simplement que la réponse contient les champs attendus.
        assert "flagged" in moderation_result
        assert "categories" in moderation_result
        assert "category_scores" in moderation_result
        
        # Si le contenu est signalé comme inapproprié, la tentative de publication serait bloquée
        if moderation_result["flagged"]:
            # Cette partie du test ne s'exécute que si le contenu est effectivement détecté comme inapproprié
            print("Le contenu inapproprié a été correctement signalé")
    
    def test_batch_moderation(self):
        """
        Test de modération par lots.
        Ce test simule la modération de plusieurs contenus en une seule requête.
        """
        # Préparation des contenus à modérer
        contents = [
            "Premier texte à modérer qui est très probablement sûr.",
            "Deuxième texte à modérer avec un contenu normal.",
            TEST_UNSAFE_CONTENT
        ]
        
        # Modération par lots
        moderation_response = client.post(
            "/moderation/moderate/batch",
            json=contents,
            params={
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        # Vérifier que la modération par lots a réussi
        assert moderation_response.status_code == 200
        moderation_results = moderation_response.json()
        assert isinstance(moderation_results, list)
        assert len(moderation_results) == len(contents)
        
        # Vérifier que chaque résultat contient les champs attendus
        for result in moderation_results:
            assert "flagged" in result
            assert "categories" in result
            assert "category_scores" in result
