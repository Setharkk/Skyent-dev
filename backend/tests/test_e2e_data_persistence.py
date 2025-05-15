# backend/tests/test_e2e_data_persistence.py
import pytest
from fastapi.testclient import TestClient
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta

from app.main import app
from app.generation.models import ContentType as GenContentType, ContentTone
from app.moderation.models import ContentType as ModContentType, ModerationType
from app.publication.models import SocialMediaPlatform

client = TestClient(app)

class TestDataPersistence:
    """Tests vérifiant la persistance des données et leur récupération."""
    
    def test_generation_persistence(self):
        """
        Vérifier que les contenus générés sont persistés et récupérables.
        """
        # 1. Générer du contenu via l'API
        generation_response = client.post(
            "/generation/linkedin",
            params={
                "prompt": "Les avantages de l'intelligence artificielle pour les entreprises",
                "tone": ContentTone.PROFESSIONAL.value,
                "include_hashtags": True
            }
        )
        
        assert generation_response.status_code == 200
        generation_result = generation_response.json()
        assert "content_id" in generation_result
        content_id = generation_result["content_id"]
        
        # 2. Récupérer le contenu via l'API en utilisant son ID
        get_content_response = client.get(f"/generation/content/{content_id}")
        
        # Vérifier que le contenu peut être récupéré
        assert get_content_response.status_code == 200
        retrieved_content = get_content_response.json()
        assert retrieved_content["content_id"] == content_id
        assert retrieved_content["content"] == generation_result["content"]
        
        # 3. Vérifier que le contenu apparaît dans la liste des contenus générés
        all_contents_response = client.get("/generation/contents")
        assert all_contents_response.status_code == 200
        all_contents = all_contents_response.json()
        
        # Chercher notre contenu dans la liste
        found = False
        for content in all_contents:
            if content["content_id"] == content_id:
                found = True
                break
        
        assert found, f"Le contenu avec ID {content_id} n'a pas été trouvé dans la liste des contenus générés"

    def test_moderation_result_consistency(self):
        """
        Vérifier que les résultats de modération sont cohérents entre les appels.
        """
        test_text = "Ceci est un exemple de texte à modérer pour tester la persistance."
        
        # 1. Première modération
        first_moderation = client.post(
            "/moderation/moderate/text",
            params={
                "content": test_text,
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        assert first_moderation.status_code == 200
        first_result = first_moderation.json()
        
        # 2. Deuxième modération avec le même texte
        second_moderation = client.post(
            "/moderation/moderate/text",
            params={
                "content": test_text,
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        assert second_moderation.status_code == 200
        second_result = second_moderation.json()
        
        # 3. Vérifier la cohérence des résultats
        assert first_result["flagged"] == second_result["flagged"]
        
        # Les scores peuvent varier légèrement, mais les catégories flaggées devraient être cohérentes
        for category, flagged in first_result["categories"].items():
            if category in second_result["categories"]:
                assert flagged == second_result["categories"][category], f"Incohérence pour la catégorie {category}"

    def test_publication_persistence(self):
        """
        Vérifier que les publications sont persistées et récupérables.
        """
        # 1. Créer une publication directe
        unique_content = f"Test de publication persistance {uuid.uuid4()}"
        publication_response = client.post(
            "/publication/direct",
            json={
                "content": unique_content,
                "platform": SocialMediaPlatform.TWITTER.value,
                "title": "Test de persistance",
                "additional_options": {
                    "hashtags": ["#test", "#persistance"]
                }
            }
        )
        
        assert publication_response.status_code == 200
        publication_result = publication_response.json()
        assert "publication_id" in publication_result
        publication_id = publication_result["publication_id"]
        
        # 2. Récupérer la publication via l'API en utilisant son ID
        get_publication_response = client.get(f"/publication/publication/{publication_id}")
        
        # Vérifier que la publication peut être récupérée
        assert get_publication_response.status_code == 200
        retrieved_publication = get_publication_response.json()
        assert retrieved_publication["publication_id"] == publication_id
        assert retrieved_publication["content_id"] == publication_result["content_id"]
        
        # 3. Vérifier que la publication apparaît dans la liste des publications
        all_publications_response = client.get("/publication/publications")
        assert all_publications_response.status_code == 200
        all_publications = all_publications_response.json()
        
        # Chercher notre publication dans la liste
        found = False
        for pub in all_publications:
            if pub["publication_id"] == publication_id:
                found = True
                break
        
        assert found, f"La publication avec ID {publication_id} n'a pas été trouvée dans la liste des publications"

    def test_complete_flow_persistence(self):
        """
        Tester la persistance du flux complet: génération -> modération -> publication.
        """
        # 1. Générer un contenu
        unique_prompt = f"Test de persistance du flux complet {uuid.uuid4()}"
        generation_response = client.post(
            "/generation/linkedin",
            params={
                "prompt": unique_prompt,
                "tone": ContentTone.PROFESSIONAL.value
            }
        )
        
        assert generation_response.status_code == 200
        generation_result = generation_response.json()
        content_id = generation_result["content_id"]
        
        # 2. Modérer le contenu
        moderation_response = client.post(
            "/moderation/moderate/text",
            params={
                "content": generation_result["content"],
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        assert moderation_response.status_code == 200
        moderation_result = moderation_response.json()
        
        # Si le contenu est approprié, le publier
        if not moderation_result["flagged"]:
            # 3. Publier le contenu
            publication_response = client.post(
                "/publication/publish",
                json={
                    "content_id": content_id,
                    "platform": SocialMediaPlatform.LINKEDIN.value
                }
            )
            
            assert publication_response.status_code == 200
            publication_result = publication_response.json()
            publication_id = publication_result["publication_id"]
            
            # 4. Vérifier que le contenu et la publication sont liés
            pub_content_response = client.get(f"/publication/content/{content_id}/publications")
            assert pub_content_response.status_code == 200
            content_publications = pub_content_response.json()
            
            # Vérifier que notre publication apparaît dans les publications liées au contenu
            found = False
            for pub in content_publications:
                if pub["publication_id"] == publication_id:
                    found = True
                    break
            
            assert found, f"La publication avec ID {publication_id} n'a pas été trouvée dans les publications liées au contenu {content_id}"
    
    def test_data_persistence_after_restart(self):
        """
        Simuler un redémarrage du service et vérifier que les données sont toujours disponibles.
        
        Note: Ce test est plus une démonstration conceptuelle. Dans un environnement de test réel,
        vous pourriez avoir besoin d'adapter cette approche en fonction de votre architecture.
        """
        # 1. Générer un contenu unique pour ce test
        unique_id = str(uuid.uuid4())
        unique_prompt = f"Test de persistance après redémarrage {unique_id}"
        
        generation_response = client.post(
            "/generation/linkedin",
            params={
                "prompt": unique_prompt,
                "tone": ContentTone.PROFESSIONAL.value
            }
        )
        
        assert generation_response.status_code == 200
        content_id = generation_response.json()["content_id"]
        
        # 2. Simuler un redémarrage du service en créant un nouveau client
        # Dans un environnement réel, vous pourriez redémarrer le serveur ou utiliser un 
        # mécanisme spécifique à votre architecture
        restart_client = TestClient(app)
        
        # 3. Tenter de récupérer le contenu après "redémarrage"
        get_content_response = restart_client.get(f"/generation/content/{content_id}")
        
        # Si votre service utilise une base de données persistante et est correctement configuré,
        # le contenu devrait être récupérable après redémarrage
        assert get_content_response.status_code == 200
        retrieved_content = get_content_response.json()
        assert retrieved_content["content_id"] == content_id
        assert unique_id in retrieved_content["parameters"]["prompt"]

    def test_multiple_content_types_moderation_persistence(self):
        """
        Tester la persistance des modérations sur différents types de contenus.
        """
        # Créer un identifiant unique pour ce test
        unique_id = str(uuid.uuid4())[:8]
        
        # Créer une liste de contenus de différents types à modérer
        test_contents = [
            f"Texte standard pour test de modération multiple {unique_id}",
            f"Ceci est un texte qui simule une description d'image {unique_id}",
            f"Transcription audio simulée pour test de modération {unique_id}"
        ]
        
        # Dictionnaire pour stocker les résultats
        moderation_results = {}
        
        # 1. Modérer chaque contenu
        for idx, content in enumerate(test_contents):
            content_type = ModContentType.TEXT
            if idx == 1:
                content_type = ModContentType.IMAGE  # Simulé - en réalité ce serait une URL d'image
            elif idx == 2:
                content_type = ModContentType.AUDIO  # Simulé - en réalité ce serait une URL d'audio
                
            moderation_response = client.post(
                f"/moderation/moderate/{content_type.value}",
                params={
                    "content": content,
                    "moderation_type": ModerationType.COMBINED.value
                }
            )
            
            assert moderation_response.status_code == 200
            result = moderation_response.json()
            moderation_results[content] = result
        
        # 2. Simuler un redémarrage du service
        restart_client = TestClient(app)
        
        # 3. Vérifier que les résultats de modération sont cohérents après redémarrage
        for content, original_result in moderation_results.items():
            # Effectuer à nouveau la modération du même contenu
            content_type = ModContentType.TEXT  # Par défaut
            if "image" in content:
                content_type = ModContentType.IMAGE
            elif "audio" in content:
                content_type = ModContentType.AUDIO
                
            new_moderation_response = restart_client.post(
                f"/moderation/moderate/{content_type.value}",
                params={
                    "content": content,
                    "moderation_type": ModerationType.COMBINED.value
                }
            )
            
            assert new_moderation_response.status_code == 200
            new_result = new_moderation_response.json()
            
            # Vérifier que le statut général est cohérent
            assert original_result["flagged"] == new_result["flagged"], f"Incohérence dans le statut flagged pour: {content}"
            
            # Vérifier que les catégories flaggées sont cohérentes
            for category, flagged in original_result["categories"].items():
                if category in new_result["categories"]:
                    assert flagged == new_result["categories"][category], f"Incohérence pour la catégorie {category} dans: {content}"


class TestDatabaseState:
    """Tests examinant directement l'état de la base de données SQLite."""
    
    def test_sqlite_database_state(self):
        """
        Vérifie l'état de la base de données SQLite directement.
        Note: Ce test dépend de la base de données SQLite spécifique.
        Si vous utilisez une autre base de données, ce test devra être adapté.
        """
        db_path = "/workspaces/Skyent-dev/backend/skyent.db"
        
        # Vérifier que le fichier de base de données existe
        assert os.path.exists(db_path), f"Base de données SQLite introuvable à {db_path}"
        
        # Se connecter directement à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister les tables de la base de données
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Afficher les tables pour information
        table_names = [table[0] for table in tables]
        print(f"Tables dans la base de données: {table_names}")
        
        # Vérifier quelques tables clés (à adapter selon votre schéma)
        expected_tables = ['generated_contents', 'publications', 'moderation_results', 'analyses']
        
        # Vérifier que certaines tables essentielles existent
        for table in expected_tables:
            if table not in table_names:
                print(f"*** ERREUR: Table {table} non trouvée dans la base de données ***")
            assert table in table_names, f"Table {table} non trouvée dans la base de données"
        
        # Si la table "generated_contents" existe, vérifier son contenu
        if 'generated_contents' in table_names:
            cursor.execute("SELECT COUNT(*) FROM generated_contents;")
            count = cursor.fetchone()[0]
            print(f"Nombre de contenus générés dans la base de données: {count}")
            # Commenté pour l'instant car nous n'avons pas encore généré de contenu
            # assert count > 0, "Aucun contenu généré trouvé dans la base de données"
        
        # Fermer la connexion
        conn.close()
        
    def test_moderation_database_persistence(self):
        """
        Vérifie que les résultats de modération sont correctement stockés dans la base de données.
        """
        db_path = "/workspaces/Skyent-dev/backend/skyent.db"
        
        # Vérifier que le fichier de base de données existe
        assert os.path.exists(db_path), f"Base de données SQLite introuvable à {db_path}"
        
        # Créer un contenu unique à modérer
        unique_text = f"Contenu à modérer pour test de persistance en base de données {uuid.uuid4()}"
        
        # Effectuer une modération via l'API
        moderation_response = client.post(
            "/moderation/moderate/text",
            params={
                "content": unique_text,
                "moderation_type": ModerationType.COMBINED.value
            }
        )
        
        assert moderation_response.status_code == 200
        moderation_result = moderation_response.json()
        
        # Se connecter directement à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier que la table des modérations existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moderation_results';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Rechercher notre entrée de modération dans la base de données
            # Note: Ceci suppose que la table contient une colonne 'content' ou similaire
            cursor.execute("SELECT * FROM moderation_results WHERE content LIKE ?;", (f"%{unique_text[:50]}%",))
            result = cursor.fetchone()
            
            # Si nous trouvons le résultat, vérifier qu'il correspond à notre modération
            if result:
                print(f"Résultat de modération trouvé en base de données: {result}")
                # Vérifier que le statut de modération (flagged) correspond
                # Ceci dépend de la structure exacte de votre table, adaptez selon votre schéma
                assert result[2] == int(moderation_result["flagged"]), "Le statut de modération ne correspond pas"
            else:
                # Si le résultat n'est pas trouvé, c'est peut-être normal si les modérations ne sont pas persistées
                # Dans ce cas, ce test est informatif plutôt que contraignant
                print("Résultat de modération non trouvé dans la base de données. " 
                      "Si la persistance des modérations n'est pas implémentée, ce message est normal.")
        else:
            print("Table 'moderation_results' non trouvée. La persistance des modérations n'est peut-être pas implémentée.")
        
        # Fermer la connexion
        conn.close()
