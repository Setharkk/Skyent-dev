# backend/app/generation/service.py
import os
import uuid
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
import json
import re
import random

# Importation des bibliothèques IA
from openai import OpenAI
from anthropic import Anthropic

from .models import (
    ContentType, 
    ContentTone, 
    GenerationParameters, 
    GeneratedContent
)

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self):
        """Initialise le service de génération avec les clients API."""
        # Initialisation du client OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY n'est pas définie. La génération avec OpenAI ne fonctionnera pas.")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Initialisation du client Anthropic
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY n'est pas définie. La génération avec Anthropic ne fonctionnera pas.")
        self.anthropic_client = Anthropic(api_key=self.anthropic_api_key) if self.anthropic_api_key else None
        
        # Stockage en mémoire des contenus générés (pour compatibilité et fallback)
        self._generated_contents = {}
        
        # Le repository sera injecté par la factory
        self.repository = None
        
    def set_repository(self, repository):
        """
        Définit le repository à utiliser pour la persistance des données.
        
        Args:
            repository: Le repository de génération
        """
        self.repository = repository

    async def generate_content(self, parameters: GenerationParameters) -> GeneratedContent:
        """
        Génère du contenu basé sur les paramètres fournis.
        
        Args:
            parameters: Paramètres de génération
            
        Returns:
            GeneratedContent: Le contenu généré
        """
        try:
            # Génération avec OpenAI par défaut
            if self.openai_client:
                result = await self._generate_with_openai(parameters)
            elif self.anthropic_client:
                result = await self._generate_with_anthropic(parameters)
            else:
                # Fallback pour les tests si aucun client n'est disponible
                result = await self._generate_mock_content(parameters)
            
            # Enregistrement du contenu généré
            content_id = str(uuid.uuid4())
            generated_content = GeneratedContent(
                content_id=content_id,
                content_type=parameters.content_type,
                content=result["content"],
                variants=result.get("variants"),
                hashtags=result.get("hashtags"),
                title=result.get("title"),
                summary=result.get("summary"),
                parameters=parameters,
                created_at=datetime.now().isoformat(),
                metadata=result.get("metadata")
            )
            
            # Stockage du contenu généré dans le dictionnaire (pour compatibilité pendant la transition)
            self._generated_contents[content_id] = generated_content
            
            # Stockage dans la base de données si le repository est disponible
            if self.repository:
                from app.db.models.generation import GeneratedContent as DbGeneratedContent
                db_content = DbGeneratedContent(
                    id=content_id,
                    content_type=parameters.content_type,
                    content=result["content"],
                    prompt=parameters.prompt,
                    tone=parameters.tone if hasattr(parameters, 'tone') else None,
                    model_used=result.get("metadata", {}).get("model") if result.get("metadata") else None
                )
                await self.repository.create(db_content)
            
            return generated_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de contenu: {str(e)}")
            raise

    async def get_content_by_id(self, content_id: str) -> Optional[GeneratedContent]:
        """
        Récupère un contenu généré par son ID.
        
        Args:
            content_id: L'identifiant du contenu
            
        Returns:
            GeneratedContent: Le contenu généré ou None s'il n'existe pas
        """
        return self._generated_contents.get(content_id)

    async def get_all_generated_contents(self) -> List[GeneratedContent]:
        """
        Récupère tous les contenus générés.
        
        Returns:
            List[GeneratedContent]: Liste des contenus générés
        """
        return list(self._generated_contents.values())

    async def _generate_with_openai(self, parameters: GenerationParameters) -> Dict[str, Any]:
        """
        Génère du contenu en utilisant l'API OpenAI.
        
        Args:
            parameters: Paramètres de génération
            
        Returns:
            Dict[str, Any]: Résultat de la génération
        """
        # Construction du prompt en fonction du type de contenu
        system_prompt = "Tu es un expert en création de contenu pour les médias sociaux et le marketing digital."
        
        # Ajout de contexte spécifique au type de contenu
        if parameters.content_type == ContentType.LINKEDIN_POST:
            system_prompt += " Tu es spécialisé dans la création de posts LinkedIn professionnels et engageants."
        elif parameters.content_type == ContentType.TWITTER_POST:
            system_prompt += " Tu es spécialisé dans la création de tweets concis et attrayants."
        elif parameters.content_type == ContentType.BLOG_ARTICLE:
            system_prompt += " Tu es spécialisé dans la rédaction d'articles de blog informatifs et bien structurés."
        
        # Intégration de la tonalité
        if parameters.tone:
            system_prompt += f" Le contenu doit avoir une tonalité {parameters.tone.value}."
        
        # Construction du prompt utilisateur
        user_prompt = f"Génère un contenu de type {parameters.content_type.value} sur le sujet suivant: {parameters.prompt}"
        
        # Ajout des contraintes supplémentaires
        constraints = []
        if parameters.keywords:
            constraints.append(f"Inclure les mots-clés suivants: {', '.join(parameters.keywords)}")
        if parameters.max_length:
            constraints.append(f"Longueur maximale: {parameters.max_length} caractères")
        if parameters.target_audience:
            constraints.append(f"Public cible: {parameters.target_audience}")
        if parameters.include_hashtags:
            constraints.append("Inclure des hashtags pertinents")
        if parameters.include_emojis:
            constraints.append("Utiliser des emojis appropriés")
        if parameters.language:
            constraints.append(f"Langue: {parameters.language}")
        if parameters.references:
            constraints.append(f"Mentionner les sources suivantes: {', '.join(parameters.references)}")
        
        if constraints:
            user_prompt += "\n\nContraintes:\n" + "\n".join([f"- {c}" for c in constraints])
        
        # Format de réponse demandé
        user_prompt += """

Réponds au format JSON suivant:
```json
{
    "content": "Le contenu principal généré",
    "variants": ["Variante 1", "Variante 2"],
    "hashtags": ["#hashtag1", "#hashtag2"],
    "title": "Titre suggéré (si applicable)",
    "summary": "Bref résumé du contenu"
}
```
"""
        
        try:
            # Appel à l'API OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",  # ou un autre modèle approprié
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Extraction du contenu généré
            response_text = response.choices[0].message.content
            
            # Parsing du JSON
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if json_match:
                content_json = json.loads(json_match.group(0))
                return content_json
            else:
                logger.warning("Format de réponse OpenAI inattendu")
                return {"content": response_text, "variants": [], "hashtags": []}
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération avec OpenAI: {str(e)}")
            raise

    async def _generate_with_anthropic(self, parameters: GenerationParameters) -> Dict[str, Any]:
        """
        Génère du contenu en utilisant l'API Anthropic.
        
        Args:
            parameters: Paramètres de génération
            
        Returns:
            Dict[str, Any]: Résultat de la génération
        """
        # Construction du prompt système pour Anthropic
        system_prompt = "Tu es un expert en création de contenu pour les médias sociaux et le marketing digital."
        
        # Logique similaire à OpenAI, adaptée à Anthropic
        if parameters.content_type == ContentType.LINKEDIN_POST:
            system_prompt += " Tu es spécialisé dans la création de posts LinkedIn professionnels et engageants."
        elif parameters.content_type == ContentType.TWITTER_POST:
            system_prompt += " Tu es spécialisé dans la création de tweets concis et attrayants."
        elif parameters.content_type == ContentType.BLOG_ARTICLE:
            system_prompt += " Tu es spécialisé dans la rédaction d'articles de blog informatifs et bien structurés."
        
        if parameters.tone:
            system_prompt += f" Le contenu doit avoir une tonalité {parameters.tone.value}."
        
        # Construction du prompt utilisateur
        user_prompt = f"Génère un contenu de type {parameters.content_type.value} sur le sujet suivant: {parameters.prompt}"
        
        # Ajout des contraintes supplémentaires (même logique que pour OpenAI)
        constraints = []
        if parameters.keywords:
            constraints.append(f"Inclure les mots-clés suivants: {', '.join(parameters.keywords)}")
        if parameters.max_length:
            constraints.append(f"Longueur maximale: {parameters.max_length} caractères")
        if parameters.target_audience:
            constraints.append(f"Public cible: {parameters.target_audience}")
        if parameters.include_hashtags:
            constraints.append("Inclure des hashtags pertinents")
        if parameters.include_emojis:
            constraints.append("Utiliser des emojis appropriés")
        if parameters.language:
            constraints.append(f"Langue: {parameters.language}")
        if parameters.references:
            constraints.append(f"Mentionner les sources suivantes: {', '.join(parameters.references)}")
        
        if constraints:
            user_prompt += "\n\nContraintes:\n" + "\n".join([f"- {c}" for c in constraints])
        
        # Format de réponse demandé
        user_prompt += """

Réponds au format JSON suivant:
```json
{
    "content": "Le contenu principal généré",
    "variants": ["Variante 1", "Variante 2"],
    "hashtags": ["#hashtag1", "#hashtag2"],
    "title": "Titre suggéré (si applicable)",
    "summary": "Bref résumé du contenu"
}
```
"""
        
        try:
            # Appel à l'API Anthropic
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extraction du contenu généré
            response_text = response.content[0].text
            
            # Parsing du JSON
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if json_match:
                content_json = json.loads(json_match.group(0))
                return content_json
            else:
                logger.warning("Format de réponse Anthropic inattendu")
                return {"content": response_text, "variants": [], "hashtags": []}
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération avec Anthropic: {str(e)}")
            raise

    async def _generate_mock_content(self, parameters: GenerationParameters) -> Dict[str, Any]:
        """
        Génère du contenu simulé pour les tests (pas d'API).
        
        Args:
            parameters: Paramètres de génération
            
        Returns:
            Dict[str, Any]: Contenu généré simulé
        """
        logger.warning("Utilisation de la génération simulée (mock) - aucune API disponible")
        
        content_types = {
            ContentType.LINKEDIN_POST: "Ceci est un exemple de post LinkedIn sur {}. #professionnel #carrière",
            ContentType.TWITTER_POST: "Tweet d'exemple sur {}! #sujet #exemple",
            ContentType.BLOG_ARTICLE: "# Article de Blog sur {}\n\nCeci est une introduction...\n\n## Point 1\n\nContenu...",
            ContentType.NEWSLETTER: "Newsletter: Les dernières nouvelles sur {}\n\nChers abonnés,\n\nAujourd'hui nous explorons...",
            ContentType.EMAIL: "Objet: Information sur {}\n\nBonjour,\n\nJe vous contacte au sujet de...",
            ContentType.PRODUCT_DESCRIPTION: "Découvrez notre produit lié à {}. Caractéristiques: ...",
        }
        
        # Contenu par défaut si le type n'est pas dans la liste
        default_content = "Contenu généré pour le sujet: {}"
        
        # Sélection du template selon le type de contenu
        template = content_types.get(parameters.content_type, default_content)
        
        # Génération du contenu principal
        content = template.format(parameters.prompt)
        
        # Génération de variantes
        variants = [
            template.format(parameters.prompt + " (variante 1)"),
            template.format(parameters.prompt + " (variante 2)")
        ]
        
        # Génération de hashtags
        hashtags = ["#exemple", "#test"]
        if parameters.keywords:
            hashtags.extend([f"#{keyword.lower().replace(' ', '')}" for keyword in parameters.keywords])
        
        # Titre et résumé si applicable
        title = f"Contenu sur {parameters.prompt}" if parameters.content_type in [
            ContentType.BLOG_ARTICLE, ContentType.NEWSLETTER, ContentType.EMAIL
        ] else None
        
        summary = f"Résumé du contenu généré sur {parameters.prompt}" if parameters.content_type in [
            ContentType.BLOG_ARTICLE, ContentType.NEWSLETTER
        ] else None
        
        return {
            "content": content,
            "variants": variants,
            "hashtags": hashtags,
            "title": title,
            "summary": summary,
            "metadata": {"mock": True}
        }


# Instance unique du service de génération
generation_service = GenerationService()
