# backend/app/publication/service.py
import os
import uuid
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import json
import re
import requests
from dotenv import load_dotenv

# Import des modèles du module de génération
from ..generation.service import generation_service
from .models import (
    PublicationRequest,
    PublicationResult,
    PublicationStatus,
    SocialMediaPlatform,
    DirectPublicationRequest
)

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logger = logging.getLogger(__name__)


class PublicationService:
    def __init__(self):
        """Initialise le service de publication."""
        # Clés API pour les différentes plateformes
        self.linkedin_api_key = os.getenv("LINKEDIN_API_KEY")
        self.twitter_api_key = os.getenv("TWITTER_API_KEY")
        self.facebook_api_key = os.getenv("FACEBOOK_API_KEY")
        
        # Stockage en mémoire des publications (à remplacer par une base de données)
        self._publication_results = {}
        
        # Le repository sera injecté par la factory
        self.repository = None
    
    def set_repository(self, repository):
        """
        Définit le repository à utiliser pour la persistance des données.
        
        Args:
            repository: Le repository de publication
        """
        self.repository = repository

    async def publish_content(self, request: PublicationRequest) -> PublicationResult:
        """
        Publie un contenu sur la plateforme spécifiée.
        
        Args:
            request: Les informations sur la publication à effectuer
            
        Returns:
            PublicationResult: Le résultat de l'opération de publication
            
        Raises:
            ValueError: Si le contenu n'est pas trouvé ou si la plateforme n'est pas supportée
        """
        # Récupération du contenu à publier
        content = await generation_service.get_content_by_id(request.content_id)
        if content is None:
            raise ValueError(f"Contenu avec ID {request.content_id} non trouvé")
        
        # Création de l'ID de publication
        publication_id = str(uuid.uuid4())
        
        # Vérification de la disponibilité de l'API pour la plateforme choisie
        if not self._check_platform_availability(request.platform):
            # Simuler une publication réussie pour les tests
            mock_result = await self._mock_publication(publication_id, request, content.content)
            return mock_result
        
        try:
            # Sélection de la méthode de publication en fonction de la plateforme
            if request.platform == SocialMediaPlatform.LINKEDIN:
                result = await self._publish_to_linkedin(publication_id, request, content.content)
            elif request.platform == SocialMediaPlatform.TWITTER:
                result = await self._publish_to_twitter(publication_id, request, content.content)
            elif request.platform == SocialMediaPlatform.FACEBOOK:
                result = await self._publish_to_facebook(publication_id, request, content.content)
            else:
                # Pour les autres plateformes non implémentées
                result = await self._mock_publication(publication_id, request, content.content)
            
            # Stockage du résultat
            self._publication_results[publication_id] = result
            
            # Stockage dans la base de données si le repository est disponible
            if self.repository:
                try:
                    from app.db.models.publication import Publication as DbPublication
                    
                    db_publication = DbPublication(
                        id=publication_id,
                        content_id=request.content_id,
                        content=content.content,  # Utiliser content.content au lieu de content
                        platform=request.platform,
                        status=result.status,
                        platform_post_id=result.platform_post_id,
                        schedule_time=request.schedule_time,
                        additional_options=request.additional_options,
                        published_at=datetime.now() if result.status == PublicationStatus.PUBLISHED else None
                    )
                    await self.repository.create(db_publication)
                    logger.info(f"Publication {publication_id} pour contenu {request.content_id} sauvegardée en base de données")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde en base de données: {str(e)}")
                    # Ne pas faire échouer la publication si la base de données échoue
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur {request.platform}: {str(e)}")
            
            # Création d'un résultat d'échec
            failure_result = PublicationResult(
                publication_id=publication_id,
                content_id=request.content_id,
                platform=request.platform,
                status=PublicationStatus.FAILED,
                error_message=str(e),
                publication_time=datetime.now().isoformat()
            )
            
            # Stockage du résultat d'échec
            self._publication_results[publication_id] = failure_result
            
            raise

    async def direct_publish(self, request: DirectPublicationRequest) -> PublicationResult:
        """
        Publie directement un contenu sans passer par la génération.
        
        Args:
            request: Les informations de publication directe
            
        Returns:
            PublicationResult: Le résultat de l'opération de publication
            
        Raises:
            ValueError: Si la plateforme n'est pas supportée
        """
        # Création des IDs
        content_id = str(uuid.uuid4())
        publication_id = str(uuid.uuid4())
        
        # Création d'une requête de publication standard
        pub_request = PublicationRequest(
            content_id=content_id,
            platform=request.platform,
            schedule_time=request.schedule_time,
            additional_options=request.additional_options
        )
        
        # Vérification de la disponibilité de l'API pour la plateforme choisie
        if not self._check_platform_availability(request.platform):
            # Simuler une publication réussie pour les tests
            mock_result = await self._mock_publication(publication_id, pub_request, request.content)
            return mock_result
        
        try:
            # Sélection de la méthode de publication en fonction de la plateforme
            if request.platform == SocialMediaPlatform.LINKEDIN:
                result = await self._publish_to_linkedin(publication_id, pub_request, request.content)
            elif request.platform == SocialMediaPlatform.TWITTER:
                result = await self._publish_to_twitter(publication_id, pub_request, request.content)
            elif request.platform == SocialMediaPlatform.FACEBOOK:
                result = await self._publish_to_facebook(publication_id, pub_request, request.content)
            else:
                # Pour les autres plateformes non implémentées
                result = await self._mock_publication(publication_id, pub_request, request.content)
            
            # Stockage du résultat en mémoire
            self._publication_results[publication_id] = result
            
            # Stockage dans la base de données si le repository est disponible
            if self.repository:
                try:
                    from app.db.models.publication import Publication as DbPublication
                    
                    logger.info(f"Sauvegarde de la publication directe {publication_id} dans la base de données")
                    db_publication = DbPublication(
                        id=publication_id,
                        content_id=content_id,
                        content=request.content,
                        platform=request.platform,
                        status=result.status,
                        platform_post_id=result.platform_post_id,
                        schedule_time=request.schedule_time,
                        additional_options=request.additional_options,
                        published_at=datetime.now() if result.status == PublicationStatus.PUBLISHED else None
                    )
                    await self.repository.create(db_publication)
                    logger.info(f"Publication directe {publication_id} sauvegardée avec succès")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de la publication dans la base de données: {str(e)}")
                    # Ne pas faire échouer la publication si la base de données échoue
            else:
                logger.warning("Aucun repository disponible, la publication ne sera pas persistante")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication directe sur {request.platform}: {str(e)}")
            
            # Création d'un résultat d'échec
            failure_result = PublicationResult(
                publication_id=publication_id,
                content_id=content_id,
                platform=request.platform,
                status=PublicationStatus.FAILED,
                error_message=str(e),
                publication_time=datetime.now().isoformat()
            )
            
            # Stockage du résultat d'échec
            self._publication_results[publication_id] = failure_result
            
            raise

    async def get_publication_by_id(self, publication_id: str) -> Optional[PublicationResult]:
        """
        Récupère une publication par son ID.
        
        Args:
            publication_id: L'identifiant de la publication
            
        Returns:
            PublicationResult: Le résultat de la publication ou None s'il n'existe pas
        """
        # Vérifier d'abord dans le dictionnaire en mémoire
        if publication_id in self._publication_results:
            logger.info(f"Publication {publication_id} trouvée en mémoire")
            return self._publication_results[publication_id]
        
        # Si non trouvé et repository disponible, chercher dans la base de données
        if self.repository:
            try:
                logger.info(f"Recherche de la publication {publication_id} dans la base de données")
                db_publication = await self.repository.get_by_id(publication_id)
                if db_publication:
                    # Convertir en modèle Pydantic
                    from app.publication.models import PublicationResult, PublicationStatus
                    result = PublicationResult(
                        publication_id=db_publication.id,
                        content_id=db_publication.content_id,
                        platform=db_publication.platform,
                        status=db_publication.status,
                        platform_post_id=db_publication.platform_post_id,
                        publication_time=db_publication.published_at.isoformat() if db_publication.published_at else None,
                        content=db_publication.content
                    )
                    logger.info(f"Publication {publication_id} trouvée dans la base de données")
                    return result
                else:
                    logger.warning(f"Publication {publication_id} non trouvée dans la base de données")
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la publication {publication_id} depuis la base de données: {str(e)}")
        else:
            logger.warning("Aucun repository disponible pour les publications")
        
        return None

    async def get_publications_by_content_id(self, content_id: str) -> List[PublicationResult]:
        """
        Récupère toutes les publications liées à un contenu.
        
        Args:
            content_id: L'identifiant du contenu
            
        Returns:
            List[PublicationResult]: Liste des publications pour ce contenu
        """
        logger.info(f"Recherche des publications pour le contenu {content_id}")
        
        # Récupérer depuis le dictionnaire en mémoire
        memory_results = [pub for pub in self._publication_results.values() if pub.content_id == content_id]
        logger.info(f"Publications trouvées en mémoire: {len(memory_results)}")
        
        # Si le repository est disponible, récupérer également depuis la base de données
        if self.repository:
            try:
                logger.info(f"Recherche des publications dans la base de données pour le contenu {content_id}")
                db_publications = await self.repository.get_by_content_id(content_id)
                logger.info(f"Publications trouvées en base de données: {len(db_publications)}")
                
                # Convertir les objets de base de données en modèles Pydantic
                from app.publication.models import PublicationResult, PublicationStatus
                for db_pub in db_publications:
                    # Vérifier si cette publication est déjà dans les résultats de la mémoire
                    if not any(mem_pub.publication_id == db_pub.id for mem_pub in memory_results):
                        pub_result = PublicationResult(
                            publication_id=db_pub.id,
                            content_id=db_pub.content_id,
                            platform=db_pub.platform,
                            status=db_pub.status,
                            platform_post_id=db_pub.platform_post_id,
                            publication_time=db_pub.published_at.isoformat() if db_pub.published_at else None,
                            content=db_pub.content
                        )
                        memory_results.append(pub_result)
                        logger.info(f"Publication {db_pub.id} ajoutée aux résultats depuis la base de données")
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des publications depuis la base de données: {str(e)}")
        else:
            logger.warning("Aucun repository disponible pour les publications")
        
        return memory_results

    async def get_all_publications(self) -> List[PublicationResult]:
        """
        Récupère toutes les publications.
        
        Returns:
            List[PublicationResult]: Liste de toutes les publications
        """
        return list(self._publication_results.values())

    def _check_platform_availability(self, platform: SocialMediaPlatform) -> bool:
        """
        Vérifie si l'API pour la plateforme spécifiée est disponible.
        
        Args:
            platform: La plateforme à vérifier
            
        Returns:
            bool: True si l'API est disponible, False sinon
        """
        if platform == SocialMediaPlatform.LINKEDIN:
            return self.linkedin_api_key is not None
        elif platform == SocialMediaPlatform.TWITTER:
            return self.twitter_api_key is not None
        elif platform == SocialMediaPlatform.FACEBOOK:
            return self.facebook_api_key is not None
        return False

    async def _publish_to_linkedin(self, publication_id: str, request: PublicationRequest, content: str) -> PublicationResult:
        """
        Publie du contenu sur LinkedIn.
        
        Args:
            publication_id: L'identifiant de la publication
            request: La demande de publication
            content: Le contenu à publier
            
        Returns:
            PublicationResult: Le résultat de la publication
            
        Note:
            Cette méthode est un placeholder. L'implémentation réelle
            nécessiterait l'utilisation de l'API LinkedIn.
        """
        if not self.linkedin_api_key:
            raise ValueError("LinkedIn API key non configurée")
            
        logger.info(f"Publication sur LinkedIn: {content[:100]}...")
        
        # Ici, il faudrait implémenter l'appel réel à l'API LinkedIn
        # Pour l'instant, on simule une publication réussie
        
        return PublicationResult(
            publication_id=publication_id,
            content_id=request.content_id,
            platform=SocialMediaPlatform.LINKEDIN,
            status=PublicationStatus.PUBLISHED,
            publication_time=datetime.now().isoformat(),
            platform_post_id="linkedin_post_123456",
            platform_post_url="https://www.linkedin.com/posts/user_post-123456",
            metadata={"api_used": True}
        )

    async def _publish_to_twitter(self, publication_id: str, request: PublicationRequest, content: str) -> PublicationResult:
        """
        Publie du contenu sur Twitter.
        
        Args:
            publication_id: L'identifiant de la publication
            request: La demande de publication
            content: Le contenu à publier
            
        Returns:
            PublicationResult: Le résultat de la publication
            
        Note:
            Cette méthode est un placeholder. L'implémentation réelle
            nécessiterait l'utilisation de l'API Twitter.
        """
        if not self.twitter_api_key:
            raise ValueError("Twitter API key non configurée")
            
        logger.info(f"Publication sur Twitter: {content[:100]}...")
        
        # Ici, il faudrait implémenter l'appel réel à l'API Twitter
        # Pour l'instant, on simule une publication réussie
        
        return PublicationResult(
            publication_id=publication_id,
            content_id=request.content_id,
            platform=SocialMediaPlatform.TWITTER,
            status=PublicationStatus.PUBLISHED,
            publication_time=datetime.now().isoformat(),
            platform_post_id="1234567890123456789",
            platform_post_url="https://twitter.com/user/status/1234567890123456789",
            metadata={"api_used": True}
        )

    async def _publish_to_facebook(self, publication_id: str, request: PublicationRequest, content: str) -> PublicationResult:
        """
        Publie du contenu sur Facebook.
        
        Args:
            publication_id: L'identifiant de la publication
            request: La demande de publication
            content: Le contenu à publier
            
        Returns:
            PublicationResult: Le résultat de la publication
            
        Note:
            Cette méthode est un placeholder. L'implémentation réelle
            nécessiterait l'utilisation de l'API Facebook.
        """
        if not self.facebook_api_key:
            raise ValueError("Facebook API key non configurée")
            
        logger.info(f"Publication sur Facebook: {content[:100]}...")
        
        # Ici, il faudrait implémenter l'appel réel à l'API Facebook
        # Pour l'instant, on simule une publication réussie
        
        return PublicationResult(
            publication_id=publication_id,
            content_id=request.content_id,
            platform=SocialMediaPlatform.FACEBOOK,
            status=PublicationStatus.PUBLISHED,
            publication_time=datetime.now().isoformat(),
            platform_post_id="fb_post_123456789",
            platform_post_url="https://www.facebook.com/user/posts/123456789",
            metadata={"api_used": True}
        )

    async def _mock_publication(self, publication_id: str, request: PublicationRequest, content: str) -> PublicationResult:
        """
        Simule une publication pour les tests ou les plateformes non supportées.
        
        Args:
            publication_id: L'identifiant de la publication
            request: La demande de publication
            content: Le contenu à publier
            
        Returns:
            PublicationResult: Le résultat de la publication simulée
        """
        logger.warning(f"Simulation de publication sur {request.platform}: {content[:100]}...")
        
        # Création d'un résultat simulé
        result = PublicationResult(
            publication_id=publication_id,
            content_id=request.content_id,
            platform=request.platform,
            status=PublicationStatus.PUBLISHED,
            publication_time=datetime.now().isoformat(),
            platform_post_id=f"mock_{request.platform}_post_{publication_id[:8]}",
            platform_post_url=f"https://www.example.com/{request.platform}/posts/{publication_id}",
            metadata={"simulated": True},
            content=content
        )
        
        # Stockage du résultat en mémoire
        self._publication_results[publication_id] = result
        
        # Stockage dans la base de données si le repository est disponible
        if self.repository:
            try:
                from app.db.models.publication import Publication as DbPublication
                
                logger.info(f"Sauvegarde de la publication simulée {publication_id} dans la base de données")
                db_publication = DbPublication(
                    id=publication_id,
                    content_id=request.content_id,
                    content=content,
                    platform=request.platform,
                    status=result.status,
                    platform_post_id=result.platform_post_id,
                    schedule_time=request.schedule_time,
                    additional_options=request.additional_options,
                    published_at=datetime.now() if result.status == PublicationStatus.PUBLISHED else None
                )
                await self.repository.create(db_publication)
                logger.info(f"Publication simulée {publication_id} sauvegardée avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de la publication simulée: {str(e)}")
        else:
            logger.warning("Aucun repository disponible, la publication simulée ne sera pas persistante")
        
        return result


# Instance unique du service de publication
publication_service = PublicationService()
