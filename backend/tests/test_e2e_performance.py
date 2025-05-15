# backend/tests/test_e2e_performance.py
import pytest
from fastapi.testclient import TestClient
import time
import statistics
from typing import List, Dict, Any
import asyncio
import json

from app.main import app
from app.generation.models import ContentType, ContentTone
from app.moderation.models import ContentType as ModContentType, ModerationType
from app.publication.models import SocialMediaPlatform

client = TestClient(app)

# Données de test pour les tests de performance
TEST_PROMPTS = [
    "Les avantages du développement durable pour les entreprises",
    "Comment l'intelligence artificielle transforme le marketing digital",
    "Les meilleures pratiques pour une stratégie de contenu efficace",
    "L'importance de la cybersécurité pour les petites entreprises",
    "Comment améliorer la productivité en télétravail"
]

class TestAPIPerformance:
    """Tests de performance pour mesurer la réactivité de l'API sous charge."""
    
    def measure_response_time(self, func) -> float:
        """
        Mesurer le temps de réponse d'une fonction.
        
        Args:
            func: La fonction à mesurer
            
        Returns:
            float: Le temps de réponse en secondes
        """
        start_time = time.time()
        func()
        end_time = time.time()
        return end_time - start_time
    
    def test_generation_response_time(self):
        """Mesurer le temps de réponse du service de génération."""
        response_times = []
        
        for prompt in TEST_PROMPTS:
            def generation_request():
                return client.post(
                    "/generation/linkedin",
                    params={
                        "prompt": prompt,
                        "tone": ContentTone.PROFESSIONAL.value
                    }
                )
            
            response_time = self.measure_response_time(generation_request)
            response_times.append(response_time)
        
        # Calcul des statistiques
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\nTemps de réponse génération - Moy: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")
        
        # Vérification des seuils acceptables (ajuster selon le contexte réel)
        assert avg_time < 10.0, f"Temps de réponse moyen trop élevé: {avg_time:.2f}s"
    
    def test_moderation_response_time(self):
        """Mesurer le temps de réponse du service de modération."""
        test_texts = [
            "Ce texte est un exemple de contenu normal qui ne devrait pas être signalé.",
            "Voici un autre exemple de texte sans contenu problématique.",
            "Ce document présente des informations factuelle sur l'entreprise.",
            "Résumé des principales réalisations du trimestre dernier.",
            "Perspectives économiques pour l'année à venir selon les experts."
        ]
        
        response_times = []
        
        for text in test_texts:
            def moderation_request():
                return client.post(
                    "/moderation/moderate/text",
                    params={
                        "content": text,
                        "moderation_type": ModerationType.COMBINED.value
                    }
                )
            
            response_time = self.measure_response_time(moderation_request)
            response_times.append(response_time)
        
        # Calcul des statistiques
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\nTemps de réponse modération - Moy: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")
        
        # Vérification des seuils acceptables (ajuster selon le contexte réel)
        assert avg_time < 5.0, f"Temps de réponse moyen trop élevé: {avg_time:.2f}s"
    
    def test_publication_response_time(self):
        """Mesurer le temps de réponse du service de publication."""
        test_contents = [
            "Publication test numéro 1 pour mesurer le temps de réponse.",
            "Publication test numéro 2 pour mesurer le temps de réponse.",
            "Publication test numéro 3 pour mesurer le temps de réponse.",
            "Publication test numéro 4 pour mesurer le temps de réponse.",
            "Publication test numéro 5 pour mesurer le temps de réponse."
        ]
        
        response_times = []
        
        for content in test_contents:
            def publication_request():
                return client.post(
                    "/publication/direct",
                    json={
                        "content": content,
                        "platform": SocialMediaPlatform.TWITTER.value,
                    }
                )
            
            response_time = self.measure_response_time(publication_request)
            response_times.append(response_time)
        
        # Calcul des statistiques
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\nTemps de réponse publication - Moy: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")
        
        # Vérification des seuils acceptables (ajuster selon le contexte réel)
        assert avg_time < 3.0, f"Temps de réponse moyen trop élevé: {avg_time:.2f}s"
    
    def test_complete_flow_response_time(self):
        """Mesurer le temps de réponse du flux complet génération > modération > publication."""
        total_times = []
        
        for prompt in TEST_PROMPTS[:2]:  # Limite à 2 pour le test complet qui est plus long
            start_time = time.time()
            
            # 1. Génération
            gen_response = client.post(
                "/generation/linkedin",
                params={
                    "prompt": prompt,
                    "tone": ContentTone.PROFESSIONAL.value
                }
            )
            
            assert gen_response.status_code == 200
            gen_result = gen_response.json()
            content = gen_result["content"]
            
            # 2. Modération
            mod_response = client.post(
                "/moderation/moderate/text",
                params={
                    "content": content,
                    "moderation_type": ModerationType.COMBINED.value
                }
            )
            
            assert mod_response.status_code == 200
            
            # 3. Publication (si non signalé)
            mod_result = mod_response.json()
            if not mod_result["flagged"]:
                pub_response = client.post(
                    "/publication/direct",
                    json={
                        "content": content,
                        "platform": SocialMediaPlatform.LINKEDIN.value,
                    }
                )
                
                assert pub_response.status_code == 200
            
            end_time = time.time()
            total_time = end_time - start_time
            total_times.append(total_time)
        
        # Calcul des statistiques
        avg_time = statistics.mean(total_times)
        max_time = max(total_times)
        min_time = min(total_times)
        
        print(f"\nTemps de réponse flux complet - Moy: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")
        
        # Vérification des seuils acceptables (ajuster selon le contexte réel)
        assert avg_time < 15.0, f"Temps de réponse moyen trop élevé: {avg_time:.2f}s"
    
    def test_batch_moderation_scaling(self):
        """
        Tester comment le temps de modération par lots évolue avec le nombre d'éléments.
        Cela permet de vérifier l'efficacité du traitement par lots.
        """
        batch_sizes = [1, 2, 5, 10]
        avg_times_per_item = []
        
        base_text = "Ceci est un texte d'exemple pour tester la modération par lots. "
        
        for size in batch_sizes:
            # Créer un lot de textes de la taille spécifiée
            batch = [f"{base_text} Item {i+1}" for i in range(size)]
            
            start_time = time.time()
            response = client.post(
                "/moderation/moderate/batch",
                json=batch,
                params={
                    "moderation_type": ModerationType.COMBINED.value
                }
            )
            end_time = time.time()
            
            assert response.status_code == 200
            
            total_time = end_time - start_time
            time_per_item = total_time / size
            avg_times_per_item.append(time_per_item)
            
            print(f"\nLot de taille {size}: Temps total {total_time:.2f}s, Temps par élément {time_per_item:.2f}s")
        
        # La modération par lots devrait être plus efficace (temps par élément diminue avec la taille du lot)
        # Cette assertion peut être ajustée en fonction du comportement réel de votre API
        if len(avg_times_per_item) > 1 and avg_times_per_item[0] > 0:
            efficiency = (avg_times_per_item[0] - avg_times_per_item[-1]) / avg_times_per_item[0]
            print(f"Gain d'efficacité du traitement par lots: {efficiency:.2%}")
            
            # Le temps par élément devrait diminuer d'au moins 10% pour le plus grand lot par rapport au lot de 1
            assert efficiency > 0.1, "Le traitement par lots n'est pas suffisamment efficace"
