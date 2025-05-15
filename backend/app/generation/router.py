# backend/app/generation/router.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any, Union

from .models import (
    GenerationParameters, 
    GeneratedContent, 
    ContentType, 
    ContentTone
)
from .service import generation_service

router = APIRouter()

@router.get("/")
async def get_generation_status():
    """Vérifier le statut du service de génération."""
    return {"module": "generation", "status": "ok"}

@router.post("/content", response_model=GeneratedContent)
async def generate_content(parameters: GenerationParameters):
    """
    Génère du contenu basé sur les paramètres fournis.
    
    Args:
        parameters: Les paramètres de génération
        
    Returns:
        GeneratedContent: Le contenu généré
        
    Raises:
        HTTPException: En cas d'erreur lors de la génération
    """
    try:
        result = await generation_service.generate_content(parameters)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")

@router.get("/content/{content_id}", response_model=GeneratedContent)
async def get_content(content_id: str):
    """
    Récupère un contenu généré par son ID.
    
    Args:
        content_id: L'identifiant du contenu
        
    Returns:
        GeneratedContent: Le contenu généré
        
    Raises:
        HTTPException: Si le contenu n'est pas trouvé
    """
    result = await generation_service.get_content_by_id(content_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Contenu avec ID {content_id} non trouvé")
    return result

@router.get("/contents", response_model=List[GeneratedContent])
async def get_all_contents():
    """
    Récupère tous les contenus générés.
    
    Returns:
        List[GeneratedContent]: Liste des contenus générés
    """
    results = await generation_service.get_all_generated_contents()
    return results

@router.post("/linkedin", response_model=GeneratedContent)
async def generate_linkedin_post(
    prompt: str,
    keywords: Optional[List[str]] = Query(None),
    tone: Optional[ContentTone] = None,
    max_length: Optional[int] = None,
    include_hashtags: bool = True,
    include_emojis: bool = True,
    target_audience: Optional[str] = None,
    language: str = "fr"
):
    """
    Point d'entrée simplifié pour la génération de posts LinkedIn.
    
    Args:
        prompt: Sujet ou description du post à générer
        keywords: Mots-clés à inclure
        tone: Tonalité du post
        max_length: Longueur maximale
        include_hashtags: Inclure des hashtags
        include_emojis: Inclure des emojis
        target_audience: Public cible
        language: Langue du contenu
        
    Returns:
        GeneratedContent: Le post LinkedIn généré
    """
    parameters = GenerationParameters(
        content_type=ContentType.LINKEDIN_POST,
        prompt=prompt,
        keywords=keywords,
        tone=tone,
        max_length=max_length,
        include_hashtags=include_hashtags,
        include_emojis=include_emojis,
        target_audience=target_audience,
        language=language
    )
    
    try:
        result = await generation_service.generate_content(parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")

@router.post("/twitter", response_model=GeneratedContent)
async def generate_twitter_post(
    prompt: str,
    keywords: Optional[List[str]] = Query(None),
    tone: Optional[ContentTone] = None,
    include_hashtags: bool = True,
    include_emojis: bool = True,
    language: str = "fr"
):
    """
    Point d'entrée simplifié pour la génération de tweets.
    
    Args:
        prompt: Sujet ou description du tweet à générer
        keywords: Mots-clés à inclure
        tone: Tonalité du tweet
        include_hashtags: Inclure des hashtags
        include_emojis: Inclure des emojis
        language: Langue du contenu
        
    Returns:
        GeneratedContent: Le tweet généré
    """
    parameters = GenerationParameters(
        content_type=ContentType.TWITTER_POST,
        prompt=prompt,
        keywords=keywords,
        tone=tone,
        max_length=280,  # Limitation Twitter
        include_hashtags=include_hashtags,
        include_emojis=include_emojis,
        language=language
    )
    
    try:
        result = await generation_service.generate_content(parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")

@router.post("/blog", response_model=GeneratedContent)
async def generate_blog_article(
    prompt: str,
    keywords: Optional[List[str]] = Query(None),
    tone: Optional[ContentTone] = None,
    max_length: Optional[int] = 5000,
    target_audience: Optional[str] = None,
    references: Optional[List[str]] = Query(None),
    language: str = "fr"
):
    """
    Point d'entrée simplifié pour la génération d'articles de blog.
    
    Args:
        prompt: Sujet ou description de l'article à générer
        keywords: Mots-clés à inclure
        tone: Tonalité de l'article
        max_length: Longueur maximale
        target_audience: Public cible
        references: Sources ou références à inclure
        language: Langue du contenu
        
    Returns:
        GeneratedContent: L'article de blog généré
    """
    parameters = GenerationParameters(
        content_type=ContentType.BLOG_ARTICLE,
        prompt=prompt,
        keywords=keywords,
        tone=tone,
        max_length=max_length,
        target_audience=target_audience,
        references=references,
        language=language
    )
    
    try:
        result = await generation_service.generate_content(parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}") 
