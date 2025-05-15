# examples/generate_and_publish.py

import os
import asyncio
from dotenv import load_dotenv

# Import des services nécessaires
from app.generation.service import generation_service
from app.generation.models import GenerationParameters, ContentType, ContentTone
from app.publication.service import publication_service
from app.publication.models import DirectPublicationRequest, SocialMediaPlatform

# Chargement des variables d'environnement
load_dotenv()

async def generate_and_publish_linkedin_post():
    """Exemple de génération et publication d'un post LinkedIn."""
    
    print("Génération d'un post LinkedIn...")
    
    # Paramètres de génération
    params = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="5 astuces pour optimiser votre profil LinkedIn et attirer des recruteurs",
        keywords=["LinkedIn", "recrutement", "profil", "optimisation", "astuces"],
        tone=ContentTone.PROFESSIONAL,
        include_hashtags=True,
        include_emojis=True,
        language="fr",
        max_length=500
    )
    
    # Génération du contenu
    result = await generation_service.generate_content(params)
    
    print(f"\nContenu généré :\n{result.content}\n")
    
    # Vérification des clés API nécessaires
    if not os.getenv("LINKEDIN_API_KEY"):
        print("⚠️ LINKEDIN_API_KEY non définie. La publication ne peut pas se faire.")
        print("Pour une vraie publication, ajoutez votre clé API dans le fichier .env")
        return
    
    # Création d'une requête de publication
    publication_request = DirectPublicationRequest(
        content=result.content,
        platform=SocialMediaPlatform.LINKEDIN,
        title="Optimisation de profil LinkedIn"
    )
    
    # Publication du contenu
    publication_result = await publication_service.publish_direct(publication_request)
    
    print(f"Publication effectuée :")
    print(f"- Statut : {publication_result.status}")
    print(f"- ID : {publication_result.publication_id}")
    if publication_result.platform_post_url:
        print(f"- URL : {publication_result.platform_post_url}")

async def generate_twitter_thread():
    """Exemple de génération d'un thread Twitter."""
    
    print("Génération d'un thread Twitter...")
    
    # Paramètres de génération
    params = GenerationParameters(
        content_type=ContentType.TWITTER_POST,
        prompt="Thread sur l'importance de l'IA dans le marketing moderne",
        keywords=["IA", "marketing", "automatisation", "personnalisation"],
        tone=ContentTone.ENTHUSIASTIC,
        include_hashtags=True,
        include_emojis=True,
        language="fr",
        max_length=1200,  # Sera divisé en plusieurs tweets
        format_options={"thread": True, "tweet_count": 5}
    )
    
    # Génération du contenu
    result = await generation_service.generate_content(params)
    
    # Le contenu est renvoyé comme un texte unique séparé par des marqueurs de tweet
    tweets = result.content.split("---TWEET---")
    
    print(f"\nThread Twitter généré ({len(tweets)} tweets) :\n")
    for i, tweet in enumerate(tweets, 1):
        print(f"Tweet {i}:\n{tweet.strip()}\n")

async def main():
    """Fonction principale exécutant les exemples."""
    print("=== EXEMPLE DE GÉNÉRATION ET PUBLICATION DE CONTENU ===\n")
    
    await generate_and_publish_linkedin_post()
    print("\n" + "="*50 + "\n")
    await generate_twitter_thread()

if __name__ == "__main__":
    asyncio.run(main())
