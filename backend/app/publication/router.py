# backend/app/publication/router.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any

from .models import (
    PublicationRequest,
    PublicationResult,
    PublicationStatus,
    SocialMediaPlatform,
    DirectPublicationRequest
)
from .service import publication_service

router = APIRouter()

@router.get("/")
async def get_publication_status():
    """Vérifier le statut du service de publication."""
    return {"module": "publication", "status": "ok"}

@router.post("/publish", response_model=PublicationResult)
async def publish_content(request: PublicationRequest):
    """
    Publie un contenu généré sur la plateforme spécifiée.
    
    Args:
        request: Les informations de publication
        
    Returns:
        PublicationResult: Le résultat de la publication
        
    Raises:
        HTTPException: En cas d'erreur lors de la publication
    """
    try:
        result = await publication_service.publish_content(request)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de publication: {str(e)}")

@router.post("/direct", response_model=PublicationResult)
async def direct_publish(request: DirectPublicationRequest):
    """
    Publie directement un contenu sans passer par la génération.
    
    Args:
        request: Les informations de publication directe
        
    Returns:
        PublicationResult: Le résultat de la publication
        
    Raises:
        HTTPException: En cas d'erreur lors de la publication
    """
    try:
        result = await publication_service.direct_publish(request)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de publication directe: {str(e)}")

@router.get("/publication/{publication_id}", response_model=PublicationResult)
async def get_publication(publication_id: str):
    """
    Récupère une publication par son ID.
    
    Args:
        publication_id: L'identifiant de la publication
        
    Returns:
        PublicationResult: Le résultat de la publication
        
    Raises:
        HTTPException: Si la publication n'est pas trouvée
    """
    result = await publication_service.get_publication_by_id(publication_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Publication avec ID {publication_id} non trouvée")
    return result

@router.get("/content/{content_id}/publications", response_model=List[PublicationResult])
async def get_content_publications(content_id: str):
    """
    Récupère toutes les publications liées à un contenu.
    
    Args:
        content_id: L'identifiant du contenu
        
    Returns:
        List[PublicationResult]: Liste des publications pour ce contenu
    """
    results = await publication_service.get_publications_by_content_id(content_id)
    return results

@router.get("/publications", response_model=List[PublicationResult])
async def get_all_publications():
    """
    Récupère toutes les publications.
    
    Returns:
        List[PublicationResult]: Liste de toutes les publications
    """
    results = await publication_service.get_all_publications()
    return results

@router.post("/linkedin", response_model=PublicationResult)
async def publish_to_linkedin(
    content: str,
    title: Optional[str] = None,
    schedule_time: Optional[str] = None
):
    """
    Point d'entrée simplifié pour la publication directe sur LinkedIn.
    
    Args:
        content: Le contenu à publier
        title: Le titre de la publication (si applicable)
        schedule_time: Date et heure de publication planifiée (format ISO)
        
    Returns:
        PublicationResult: Le résultat de la publication
    """
    request = DirectPublicationRequest(
        content=content,
        platform=SocialMediaPlatform.LINKEDIN,
        title=title,
        schedule_time=schedule_time
    )
    
    try:
        result = await publication_service.direct_publish(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de publication sur LinkedIn: {str(e)}")

@router.post("/twitter", response_model=PublicationResult)
async def publish_to_twitter(
    content: str,
    media_urls: Optional[List[str]] = Query(None),
    schedule_time: Optional[str] = None
):
    """
    Point d'entrée simplifié pour la publication directe sur Twitter.
    
    Args:
        content: Le contenu à publier
        media_urls: URLs des médias à joindre (images, vidéos)
        schedule_time: Date et heure de publication planifiée (format ISO)
        
    Returns:
        PublicationResult: Le résultat de la publication
    """
    request = DirectPublicationRequest(
        content=content,
        platform=SocialMediaPlatform.TWITTER,
        media_urls=media_urls,
        schedule_time=schedule_time
    )
    
    try:
        result = await publication_service.direct_publish(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de publication sur Twitter: {str(e)}")

@router.post("/facebook", response_model=PublicationResult)
async def publish_to_facebook(
    content: str,
    title: Optional[str] = None,
    media_urls: Optional[List[str]] = Query(None),
    schedule_time: Optional[str] = None
):
    """
    Point d'entrée simplifié pour la publication directe sur Facebook.
    
    Args:
        content: Le contenu à publier
        title: Le titre de la publication
        media_urls: URLs des médias à joindre (images, vidéos)
        schedule_time: Date et heure de publication planifiée (format ISO)
        
    Returns:
        PublicationResult: Le résultat de la publication
    """
    request = DirectPublicationRequest(
        content=content,
        platform=SocialMediaPlatform.FACEBOOK,
        title=title,
        media_urls=media_urls,
        schedule_time=schedule_time
    )
    
    try:
        result = await publication_service.direct_publish(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de publication sur Facebook: {str(e)}")

@router.post("/generate-and-publish/linkedin", response_model=PublicationResult)
async def generate_and_publish_linkedin(
    prompt: str,
    keywords: Optional[List[str]] = Query(None),
    include_hashtags: bool = True,
    schedule_time: Optional[str] = None
):
    """
    Génère et publie automatiquement un post LinkedIn.
    
    Args:
        prompt: Sujet ou description du post à générer
        keywords: Mots-clés à inclure
        include_hashtags: Inclure des hashtags
        schedule_time: Date et heure de publication planifiée (format ISO)
        
    Returns:
        PublicationResult: Le résultat de la publication
    """
    # Import du service de génération ici pour éviter les imports circulaires
    from ..generation.service import generation_service
    from ..generation.models import GenerationParameters, ContentType, ContentTone
    
    try:
        # Génération du contenu
        generation_params = GenerationParameters(
            content_type=ContentType.LINKEDIN_POST,
            prompt=prompt,
            keywords=keywords,
            tone=ContentTone.PROFESSIONAL,
            include_hashtags=include_hashtags,
            language="fr"
        )
        
        generated_content = await generation_service.generate_content(generation_params)
        
        # Création de la requête de publication
        pub_request = PublicationRequest(
            content_id=generated_content.content_id,
            platform=SocialMediaPlatform.LINKEDIN,
            schedule_time=schedule_time
        )
        
        # Publication du contenu
        result = await publication_service.publish_content(pub_request)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération et publication: {str(e)}")
