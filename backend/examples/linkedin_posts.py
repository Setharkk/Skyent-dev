# examples/linkedin_posts.py

import asyncio
from dotenv import load_dotenv

# Import des services nécessaires
from app.generation.service import generation_service
from app.generation.models import GenerationParameters, ContentType, ContentTone

# Chargement des variables d'environnement
load_dotenv()

async def generate_linkedin_posts():
    """Génère différents types de posts LinkedIn."""
    
    print("=== EXEMPLES DE POSTS LINKEDIN ===\n")
    
    # Exemple 1: Post professionnel sur un lancement de produit
    print("1. Post de lancement de produit")
    params1 = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Annonce du lancement de notre nouvelle plateforme SaaS d'analyse de données",
        keywords=["SaaS", "analyse de données", "business intelligence", "lancement"],
        tone=ContentTone.PROFESSIONAL,
        include_hashtags=True,
        include_emojis=True,
        language="fr",
        max_length=400
    )
    
    result1 = await generation_service.generate_content(params1)
    print(f"\n{result1.content}\n")
    print("-" * 50)
    
    # Exemple 2: Partage d'expertise et conseils
    print("\n2. Post de partage d'expertise")
    params2 = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="5 conseils pour améliorer la cybersécurité de votre entreprise",
        keywords=["cybersécurité", "entreprise", "sécurité informatique", "conseils"],
        tone=ContentTone.INFORMATIVE,
        include_hashtags=True,
        include_emojis=True,
        language="fr",
        max_length=500
    )
    
    result2 = await generation_service.generate_content(params2)
    print(f"\n{result2.content}\n")
    print("-" * 50)
    
    # Exemple 3: Célébration d'une réussite d'entreprise
    print("\n3. Post célébrant une réussite d'entreprise")
    params3 = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Notre entreprise vient d'être nommée dans le top 10 des startups françaises à suivre",
        keywords=["réussite", "startup", "croissance", "reconnaissance"],
        tone=ContentTone.ENTHUSIASTIC,
        include_hashtags=True,
        include_emojis=True,
        language="fr",
        max_length=350
    )
    
    result3 = await generation_service.generate_content(params3)
    print(f"\n{result3.content}\n")
    print("-" * 50)
    
    # Exemple 4: Offre d'emploi
    print("\n4. Post pour une offre d'emploi")
    params4 = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="Nous recrutons un Lead Developer Full Stack à Paris",
        keywords=["recrutement", "développeur", "tech", "opportunité"],
        tone=ContentTone.PROFESSIONAL,
        include_hashtags=True,
        include_emojis=True,
        language="fr",
        max_length=400,
        format_options={"include_call_to_action": True}
    )
    
    result4 = await generation_service.generate_content(params4)
    print(f"\n{result4.content}\n")
    print("-" * 50)
    
    # Exemple 5: Réflexion sur une tendance du marché
    print("\n5. Post sur une tendance du marché")
    params5 = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt="L'essor de l'IA générative et son impact sur le marketing digital",
        keywords=["IA générative", "marketing digital", "tendances", "innovation"],
        tone=ContentTone.THOUGHTFUL,
        include_hashtags=True,
        include_emojis=False,
        language="fr",
        max_length=450
    )
    
    result5 = await generation_service.generate_content(params5)
    print(f"\n{result5.content}\n")

async def main():
    await generate_linkedin_posts()

if __name__ == "__main__":
    asyncio.run(main())
