# examples/generate_with_moderation.py

import os
import asyncio
from dotenv import load_dotenv

# Import des services nécessaires
from app.generation.service import generation_service
from app.generation.models import GenerationParameters, ContentType, ContentTone
from app.moderation.service import moderation_service
from app.moderation.models import ModerationType

# Chargement des variables d'environnement
load_dotenv()

async def generate_and_moderate_content():
    """Génère du contenu et le modère avant publication."""
    
    print("=== GÉNÉRATION DE CONTENU AVEC MODÉRATION ===\n")
    
    # Paramètres de génération
    params = GenerationParameters(
        content_type=ContentType.BLOG_ARTICLE,
        prompt="Les risques et bénéfices de l'intelligence artificielle dans notre société",
        keywords=["IA", "éthique", "avenir", "technologie", "risques"],
        tone=ContentTone.INFORMATIVE,
        language="fr",
        max_length=1000
    )
    
    # Génération du contenu
    print("Génération du contenu...")
    result = await generation_service.generate_content(params)
    
    print(f"\nContenu généré :\n{result.content[:300]}...\n")
    
    # Modération du contenu
    print("Modération du contenu généré...")
    moderation_result = await moderation_service.moderate_content(
        content=result.content,
        moderation_type=ModerationType.COMBINED
    )
    
    # Affichage des résultats de modération
    print("\nRésultats de modération :")
    print(f"- Contenu flaggé : {moderation_result.flagged}")
    
    if moderation_result.flagged:
        print("- Catégories détectées :")
        for category, is_flagged in moderation_result.categories.items():
            if is_flagged:
                score = moderation_result.category_scores.get(category, 0)
                print(f"  * {category}: {score:.4f}")
        
        print("\n⚠️ Le contenu a été flaggé et ne devrait pas être publié sans révision.")
    else:
        print("✅ Le contenu a passé la modération et peut être publié.")

async def main():
    await generate_and_moderate_content()

if __name__ == "__main__":
    asyncio.run(main())
