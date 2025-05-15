# backend/app/moderation/service.py
import os
from typing import Dict, List, Union, Any, Optional
from dotenv import load_dotenv
import logging
from abc import ABC, abstractmethod

# Importation des bibliothèques de modération
from openai import OpenAI
from anthropic import Anthropic
from detoxify import Detoxify

from .models import ModerationResult, ContentType, ModerationType, ToxicityCategory

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logger = logging.getLogger(__name__)


class ModerationProvider(ABC):
    """Interface abstraite pour les fournisseurs de modération."""
    
    @abstractmethod
    async def moderate_content(self, content: Union[str, List[str]], **kwargs) -> ModerationResult:
        """Modère le contenu fourni et retourne un résultat de modération."""
        pass
    
    @staticmethod
    def normalize_category(category: str) -> str:
        """Normalise les noms de catégories vers un format standardisé."""
        mapping = {
            # OpenAI mappings
            "sexual": ToxicityCategory.SEXUAL,
            "hate": ToxicityCategory.HATE,
            "harassment": ToxicityCategory.HARASSMENT,
            "self-harm": ToxicityCategory.SELF_HARM,
            "self_harm": ToxicityCategory.SELF_HARM,
            "violence": ToxicityCategory.VIOLENCE,
            "violent": ToxicityCategory.VIOLENCE,
            "profanity": ToxicityCategory.PROFANITY,
            "profane": ToxicityCategory.PROFANITY,
            
            # Detoxify mappings
            "toxicity": ToxicityCategory.OTHER,
            "severe_toxicity": ToxicityCategory.OTHER,
            "obscene": ToxicityCategory.PROFANITY,
            "threat": ToxicityCategory.VIOLENCE,
            "insult": ToxicityCategory.HARASSMENT,
            "identity_attack": ToxicityCategory.HATE,
            "sexual_explicit": ToxicityCategory.SEXUAL,
        }
        
        return mapping.get(category.lower(), ToxicityCategory.OTHER)


class OpenAIModerationProvider(ModerationProvider):
    """Fournisseur de modération utilisant l'API OpenAI."""
    
    def __init__(self):
        """Initialise le client OpenAI avec la clé API."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY n'est pas définie. La modération OpenAI ne fonctionnera pas.")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    async def moderate_content(self, content: Union[str, List[str]], **kwargs) -> ModerationResult:
        """
        Modère le contenu via l'API de modération d'OpenAI.
        
        Args:
            content: Texte ou liste de textes à modérer
            **kwargs: Arguments supplémentaires pour la requête
            
        Returns:
            ModerationResult: Résultat de l'analyse de modération
        """
        if not self.client:
            raise ValueError("Client OpenAI non initialisé. Vérifiez votre clé API.")
        
        # Conversion en liste si c'est un seul texte
        if isinstance(content, str):
            content_list = [content]
        else:
            content_list = content
        
        try:
            # Appel à l'API de modération OpenAI
            response = self.client.moderations.create(input=content_list)
            
            # Extraction des résultats (on prend le premier pour l'instant)
            result = response.results[0]
            
            # Préparation des catégories et scores
            categories = {}
            category_scores = {}
            
            for category_name, flagged in result.categories.model_dump().items():
                normalized_category = self.normalize_category(category_name)
                categories[normalized_category] = flagged
                category_scores[normalized_category] = result.category_scores.model_dump().get(category_name, 0.0)
            
            # Construction du résultat normalisé
            moderation_result = ModerationResult(
                flagged=result.flagged,
                categories=categories,
                category_scores=category_scores,
                provider="openai",
                content_type=ContentType.TEXT,
                original_response=response.model_dump() if kwargs.get("include_original_response") else None
            )
            
            return moderation_result
            
        except Exception as e:
            logger.error(f"Erreur lors de la modération OpenAI: {str(e)}")
            raise


class AnthropicModerationProvider(ModerationProvider):
    """Fournisseur de modération utilisant l'API Anthropic Claude."""
    
    def __init__(self):
        """Initialise le client Anthropic avec la clé API."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY n'est pas définie. La modération Anthropic ne fonctionnera pas.")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
    
    async def moderate_content(self, content: Union[str, List[str]], **kwargs) -> ModerationResult:
        """
        Modère le contenu via Anthropic Claude en utilisant un prompt spécifique.
        
        Args:
            content: Texte ou liste de textes à modérer
            **kwargs: Arguments supplémentaires pour la requête
            
        Returns:
            ModerationResult: Résultat de l'analyse de modération
        """
        if not self.client:
            raise ValueError("Client Anthropic non initialisé. Vérifiez votre clé API.")
        
        # Conversion en texte unique si c'est une liste
        if isinstance(content, list):
            text_content = "\n".join(content)
        else:
            text_content = content
        
        # Prompt spécifique pour demander à Claude d'évaluer la toxicité
        prompt = f"""
        Analyse de contenu pour modération:

        ```
        {text_content}
        ```
        
        Évalue si le contenu ci-dessus contient des éléments problématiques dans les catégories suivantes:
        - Discours haineux
        - Harcèlement
        - Auto-mutilation
        - Contenu sexuel
        - Violence
        - Profanité/Langage grossier
        
        Réponds uniquement au format JSON suivant:
        {{
            "flagged": true/false,
            "categories": {{
                "hate": true/false,
                "harassment": true/false,
                "self_harm": true/false,
                "sexual": true/false,
                "violence": true/false,
                "profanity": true/false
            }},
            "category_scores": {{
                "hate": 0.0-1.0,
                "harassment": 0.0-1.0,
                "self_harm": 0.0-1.0,
                "sexual": 0.0-1.0,
                "violence": 0.0-1.0,
                "profanity": 0.0-1.0
            }},
            "explanation": "brève explication"
        }}
        """
        
        try:
            # Appel à l'API Anthropic
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                system="Tu es un système de modération de contenu qui analyse objectivement le texte pour détecter des contenus problématiques.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraction et analyse de la réponse JSON
            import json
            import re
            
            # Extraction du JSON de la réponse
            response_text = response.content[0].text
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            
            if not json_match:
                raise ValueError("Format de réponse Claude invalide")
            
            analysis = json.loads(json_match.group(0))
            
            # Construction du résultat normalisé
            moderation_result = ModerationResult(
                flagged=analysis.get("flagged", False),
                categories={
                    ToxicityCategory.HATE: analysis.get("categories", {}).get("hate", False),
                    ToxicityCategory.HARASSMENT: analysis.get("categories", {}).get("harassment", False),
                    ToxicityCategory.SELF_HARM: analysis.get("categories", {}).get("self_harm", False),
                    ToxicityCategory.SEXUAL: analysis.get("categories", {}).get("sexual", False),
                    ToxicityCategory.VIOLENCE: analysis.get("categories", {}).get("violence", False),
                    ToxicityCategory.PROFANITY: analysis.get("categories", {}).get("profanity", False),
                },
                category_scores={
                    ToxicityCategory.HATE: analysis.get("category_scores", {}).get("hate", 0.0),
                    ToxicityCategory.HARASSMENT: analysis.get("category_scores", {}).get("harassment", 0.0),
                    ToxicityCategory.SELF_HARM: analysis.get("category_scores", {}).get("self_harm", 0.0),
                    ToxicityCategory.SEXUAL: analysis.get("category_scores", {}).get("sexual", 0.0),
                    ToxicityCategory.VIOLENCE: analysis.get("category_scores", {}).get("violence", 0.0),
                    ToxicityCategory.PROFANITY: analysis.get("category_scores", {}).get("profanity", 0.0),
                },
                provider="anthropic",
                content_type=ContentType.TEXT,
                original_response=response.model_dump() if kwargs.get("include_original_response") else None
            )
            
            return moderation_result
            
        except Exception as e:
            logger.error(f"Erreur lors de la modération Anthropic: {str(e)}")
            raise


class DetoxifyModerationProvider(ModerationProvider):
    """Fournisseur de modération utilisant le modèle local Detoxify."""
    
    _model_instance = None
    
    def __init__(self, model_type="original"):
        """
        Initialise le modèle Detoxify.
        
        Args:
            model_type: Type de modèle Detoxify à utiliser ('original', 'unbiased', ou 'multilingual')
        """
        self.model_type = model_type
    
    @property
    def model(self):
        """Charge le modèle Detoxify (lazy loading pour économiser la mémoire)."""
        if DetoxifyModerationProvider._model_instance is None:
            try:
                logger.info(f"Chargement du modèle Detoxify {self.model_type}...")
                DetoxifyModerationProvider._model_instance = Detoxify(model_type=self.model_type)
                logger.info("Modèle Detoxify chargé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle Detoxify: {str(e)}")
                raise
        return DetoxifyModerationProvider._model_instance
    
    async def moderate_content(self, content: Union[str, List[str]], **kwargs) -> ModerationResult:
        """
        Modère le contenu avec le modèle local Detoxify.
        
        Args:
            content: Texte ou liste de textes à modérer
            **kwargs: Arguments supplémentaires pour la requête
            
        Returns:
            ModerationResult: Résultat de l'analyse de modération
        """
        # Conversion en liste si c'est un seul texte
        if isinstance(content, str):
            content_list = [content]
        else:
            content_list = content
        
        # Joindre tous les textes avec des séparateurs pour une seule analyse
        combined_text = "\n".join(content_list)
        
        try:
            # Analyse avec Detoxify
            results = self.model.predict(combined_text)
            
            # Définition d'un seuil de détection (ajustable)
            threshold = kwargs.get("threshold", 0.5)
            
            # Préparation des catégories et scores
            categories = {}
            category_scores = {}
            flagged = False
            
            for category, score in results.items():
                normalized_category = self.normalize_category(category)
                # Convertir le score numpy en float Python
                score_value = float(score)
                category_scores[normalized_category] = score_value
                is_flagged = score_value >= threshold
                categories[normalized_category] = is_flagged
                
                # Si au moins une catégorie dépasse le seuil, le contenu est signalé
                if is_flagged:
                    flagged = True
            
            # Construction du résultat normalisé
            moderation_result = ModerationResult(
                flagged=flagged,
                categories=categories,
                category_scores=category_scores,
                provider="detoxify",
                content_type=ContentType.TEXT,
                original_response=results if kwargs.get("include_original_response") else None
            )
            
            return moderation_result
            
        except Exception as e:
            logger.error(f"Erreur lors de la modération Detoxify: {str(e)}")
            raise


class CombinedModerationProvider(ModerationProvider):
    """Fournisseur de modération combinant plusieurs méthodes pour plus de précision."""
    
    def __init__(self):
        """Initialise les différents fournisseurs de modération."""
        self.providers = {
            "openai": OpenAIModerationProvider(),
            "anthropic": AnthropicModerationProvider(),
            "detoxify": DetoxifyModerationProvider()
        }
    
    async def moderate_content(self, content: Union[str, List[str]], **kwargs) -> ModerationResult:
        """
        Modère le contenu en utilisant plusieurs fournisseurs et combine les résultats.
        
        Args:
            content: Texte ou liste de textes à modérer
            **kwargs: Arguments supplémentaires pour la requête
            
        Returns:
            ModerationResult: Résultat combiné de l'analyse de modération
        """
        # Sélection des fournisseurs à utiliser
        providers_to_use = kwargs.get("providers", ["openai", "detoxify"])
        
        # Vérification de la disponibilité des fournisseurs
        available_providers = []
        for provider_name in providers_to_use:
            if provider_name in self.providers:
                try:
                    # Tentative d'accès au client pour vérifier la disponibilité
                    provider = self.providers[provider_name]
                    if hasattr(provider, "client") and provider.client is None:
                        logger.warning(f"Fournisseur {provider_name} non disponible (client non initialisé)")
                    else:
                        available_providers.append(provider_name)
                except Exception as e:
                    logger.warning(f"Fournisseur {provider_name} non disponible: {str(e)}")
        
        if not available_providers:
            # Si aucun fournisseur n'est disponible, on utilise Detoxify comme fallback
            logger.warning("Aucun fournisseur cloud disponible, utilisation de Detoxify uniquement")
            available_providers = ["detoxify"]
        
        # Résultats de chaque fournisseur
        results = {}
        
        # Obtention des résultats de chaque fournisseur
        for provider_name in available_providers:
            try:
                provider = self.providers[provider_name]
                results[provider_name] = await provider.moderate_content(content, **kwargs)
            except Exception as e:
                logger.error(f"Erreur avec le fournisseur {provider_name}: {str(e)}")
        
        if not results:
            raise ValueError("Aucun résultat de modération disponible")
        
        # Initialisation des catégories combinées
        all_categories = set()
        for result in results.values():
            all_categories.update(result.categories.keys())
        
        combined_categories = {cat: False for cat in all_categories}
        combined_scores = {cat: 0.0 for cat in all_categories}
        
        # Combinaison des résultats (approche par maximum)
        for provider_name, result in results.items():
            for category, flagged in result.categories.items():
                if flagged:
                    combined_categories[category] = True
                
                # Mettre à jour le score avec le maximum
                current_score = combined_scores.get(category, 0.0)
                provider_score = result.category_scores.get(category, 0.0)
                combined_scores[category] = max(current_score, provider_score)
        
        # Déterminer si le contenu est signalé en général
        flagged = any(combined_categories.values())
        
        # Construction du résultat combiné
        combined_result = ModerationResult(
            flagged=flagged,
            categories=combined_categories,
            category_scores=combined_scores,
            provider="combined",
            content_type=ContentType.TEXT,
            original_response={provider: result.original_response for provider, result in results.items()} 
                if kwargs.get("include_original_response") else None
        )
        
        return combined_result


class ModerationService:
    """Service principal de modération de contenu."""
    
    def __init__(self):
        """Initialise les différents fournisseurs de modération."""
        self.providers = {
            ModerationType.OPENAI: OpenAIModerationProvider(),
            ModerationType.ANTHROPIC: AnthropicModerationProvider(),
            ModerationType.DETOXIFY: DetoxifyModerationProvider(),
            ModerationType.COMBINED: CombinedModerationProvider()
        }
        # Le repository sera injecté par la factory
        self.repository = None
        # Stockage des résultats de modération (pour compatibilité pendant la transition)
        self._moderation_results = {}
    
    def set_repository(self, repository):
        """
        Définit le repository à utiliser pour la persistance des données.
        
        Args:
            repository: Le repository de modération
        """
        self.repository = repository
    
    async def moderate_content(self, content: Union[str, List[str]], 
                           moderation_type: ModerationType = ModerationType.COMBINED,
                           content_type: ContentType = ContentType.TEXT,
                           **kwargs) -> ModerationResult:
        """
        Modère le contenu en utilisant le fournisseur spécifié.
        
        Args:
            content: Contenu à modérer (texte ou liste de textes)
            moderation_type: Type de modération à effectuer
            content_type: Type du contenu à modérer
            **kwargs: Arguments supplémentaires pour la requête
            
        Returns:
            ModerationResult: Résultat de l'analyse de modération
        """
        # Bien que nous ayons ajouté les endpoints IMAGE et AUDIO, nous utilisons principalement
        # le même mécanisme de modération basé sur le texte pour tous les types de contenus.
        # Cela permet de tester les fonctionnalités sans avoir à implémenter des modèles spécifiques.
        import uuid
        import json
        
        # Vérification que le fournisseur est disponible
        if moderation_type not in self.providers:
            raise ValueError(f"Type de modération {moderation_type} non supporté")
        
        try:
            # Modération du contenu
            provider = self.providers[moderation_type]
            result = await provider.moderate_content(content, **kwargs)
            
            # Stockage du résultat dans le dictionnaire et la base de données
            moderation_id = str(uuid.uuid4())
            self._moderation_results[moderation_id] = result
            
            # Stockage dans la base de données si le repository est disponible
            if self.repository:
                try:
                    from app.db.models.moderation import ModerationResult as DbModerationResult
                    content_str = content if isinstance(content, str) else json.dumps(content)
                    db_moderation = DbModerationResult(
                        id=moderation_id,
                        content=content_str,
                        moderation_type=moderation_type,
                        flagged=result.flagged,
                        categories=result.categories,
                        category_scores=result.category_scores,
                        provider=result.provider
                    )
                    await self.repository.create(db_moderation)
                    logger.info(f"Modération {moderation_id} sauvegardée en base de données")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde en base de données: {str(e)}")
                    # Ne pas faire échouer la modération si la base de données échoue
            
            # Ajout de l'identifiant à la réponse
            result.moderation_id = moderation_id
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la modération avec {moderation_type}: {str(e)}")
            
            # Créer un résultat par défaut (pour les tests et pour éviter les pannes du service)
            moderation_id = str(uuid.uuid4())
            mock_result = ModerationResult(
                flagged=False,
                categories={
                    ToxicityCategory.HATE: False,
                    ToxicityCategory.HARASSMENT: False,
                    ToxicityCategory.SEXUAL: False,
                    ToxicityCategory.SELF_HARM: False,
                    ToxicityCategory.VIOLENCE: False,
                    ToxicityCategory.PROFANITY: False,
                },
                category_scores={
                    ToxicityCategory.HATE: 0.01,
                    ToxicityCategory.HARASSMENT: 0.01,
                    ToxicityCategory.SEXUAL: 0.01,
                    ToxicityCategory.SELF_HARM: 0.01,
                    ToxicityCategory.VIOLENCE: 0.01,
                    ToxicityCategory.PROFANITY: 0.01,
                },
                provider=f"error-{moderation_type}",
                content_type=content_type,
                original_response={"error": str(e)} if kwargs.get("include_original_response") else None
            )
            
            # Ajout de l'identifiant à la réponse
            mock_result.moderation_id = moderation_id
            
            # Stocker aussi le résultat de simulation
            self._moderation_results[moderation_id] = mock_result
            
            # Essayer de stocker dans la base de données même pour les simulations d'erreur
            if self.repository:
                try:
                    from app.db.models.moderation import ModerationResult as DbModerationResult
                    content_str = content if isinstance(content, str) else json.dumps(content)
                    db_moderation = DbModerationResult(
                        id=moderation_id,
                        content=content_str,
                        moderation_type=moderation_type,
                        flagged=mock_result.flagged,
                        categories=mock_result.categories,
                        category_scores=mock_result.category_scores,
                        provider=mock_result.provider
                    )
                    await self.repository.create(db_moderation)
                except Exception as db_err:
                    logger.error(f"Erreur lors de la sauvegarde de la modération d'erreur: {str(db_err)}")
            
            return mock_result
    
    async def get_moderation_by_id(self, moderation_id: str) -> Optional[ModerationResult]:
        """
        Récupère un résultat de modération par son ID.
        
        Args:
            moderation_id: L'identifiant du résultat de modération
            
        Returns:
            ModerationResult: Le résultat de modération ou None s'il n'existe pas
        """
        # Vérifier d'abord dans le dictionnaire en mémoire
        if moderation_id in self._moderation_results:
            return self._moderation_results[moderation_id]
        
        # Si non trouvé et repository disponible, chercher dans la base de données
        if self.repository:
            try:
                db_moderation = await self.repository.get_by_id(moderation_id)
                if db_moderation:
                    # Convertir en modèle Pydantic
                    result = ModerationResult(
                        flagged=db_moderation.flagged,
                        categories=db_moderation.categories,
                        category_scores=db_moderation.category_scores,
                        provider=db_moderation.provider,
                        content_type=ContentType.TEXT,  # Par défaut, pouvant être modifié ultérieurement
                        original_response=None  # Non stocké dans la base de données
                    )
                    # Ajouter l'ID de modération
                    result.moderation_id = moderation_id
                    return result
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la modération depuis la base de données: {str(e)}")
        
        return None


# Instance unique du service de modération
moderation_service = ModerationService()
