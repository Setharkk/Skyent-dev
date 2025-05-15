# backend/app/moderation/router.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Union, Optional

from .models import ModerationRequest, ModerationResult, ContentType, ModerationType
from .service import moderation_service

router = APIRouter()

@router.get("/")
async def get_moderation_status():
    """Vérifier le statut du service de modération."""
    return {"module": "moderation", "status": "ok"}

@router.post("/moderate", response_model=ModerationResult)
async def moderate_content(request: ModerationRequest):
    """
    Modère le contenu fourni pour détecter tout élément problématique.
    
    Args:
        request: Les informations de la demande de modération
        
    Returns:
        ModerationResult: Le résultat de la modération
        
    Raises:
        HTTPException: En cas d'erreur lors de la modération
    """
    try:
        result = await moderation_service.moderate_content(
            content=request.content,
            moderation_type=request.moderation_type,
            content_type=request.content_type,
            include_original_response=request.include_original_response
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de modération: {str(e)}")

@router.post("/moderate/text", response_model=ModerationResult)
async def moderate_text(content: str, 
                     moderation_type: ModerationType = ModerationType.COMBINED, 
                     include_original_response: bool = False):
    """
    Point d'entrée simplifié pour la modération de texte.
    
    Args:
        content: Le texte à modérer
        moderation_type: Le type de modération à utiliser
        include_original_response: Inclure la réponse brute du fournisseur
        
    Returns:
        ModerationResult: Le résultat de la modération
    """
    try:
        result = await moderation_service.moderate_content(
            content=content,
            moderation_type=moderation_type,
            content_type=ContentType.TEXT,
            include_original_response=include_original_response
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de modération: {str(e)}")

@router.post("/moderate/batch", response_model=List[ModerationResult])
async def moderate_batch(contents: List[str], 
                       moderation_type: ModerationType = ModerationType.COMBINED,
                       include_original_response: bool = False):
    """
    Modère une liste de textes et retourne les résultats pour chacun.
    
    Args:
        contents: Liste de textes à modérer
        moderation_type: Le type de modération à utiliser
        include_original_response: Inclure la réponse brute du fournisseur
        
    Returns:
        List[ModerationResult]: Les résultats de modération pour chaque texte
    """
    results = []
    
    for content in contents:
        try:
            result = await moderation_service.moderate_content(
                content=content,
                moderation_type=moderation_type,
                content_type=ContentType.TEXT,
                include_original_response=include_original_response
            )
            results.append(result)
        except Exception as e:
            # En cas d'erreur, on ajoute un résultat d'erreur
            error_result = ModerationResult(
                flagged=True,
                categories={},
                category_scores={},
                provider=f"error-{moderation_type}",
                content_type=ContentType.TEXT,
                original_response={"error": str(e)} if include_original_response else None
            )
            results.append(error_result)
    
    return results

@router.post("/moderate/image", response_model=ModerationResult)
async def moderate_image(content: str, 
                       moderation_type: ModerationType = ModerationType.COMBINED,
                       include_original_response: bool = False):
    """
    Modère une image (URL ou description) et retourne le résultat.
    
    Args:
        content: URL de l'image ou description textuelle à modérer
        moderation_type: Le type de modération à utiliser
        include_original_response: Inclure la réponse brute du fournisseur
        
    Returns:
        ModerationResult: Le résultat de la modération
    """
    try:
        # Pour les tests, nous traitons simplement le texte comme la description d'une image
        # En production, cette méthode traiterait le contenu comme une URL d'image
        # ou des données binaires d'image et utiliserait un service de modération d'images
        
        # Simulation de modération d'image pour les tests
        result = await moderation_service.moderate_content(
            content=content,
            moderation_type=moderation_type,
            content_type=ContentType.IMAGE,  # Indique que c'est une image
            include_original_response=include_original_response
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de modération d'image: {str(e)}")

@router.post("/moderate/audio", response_model=ModerationResult)
async def moderate_audio(content: str, 
                       moderation_type: ModerationType = ModerationType.COMBINED,
                       include_original_response: bool = False):
    """
    Modère un fichier audio (URL ou transcription) et retourne le résultat.
    
    Args:
        content: URL de l'audio ou transcription textuelle à modérer
        moderation_type: Le type de modération à utiliser
        include_original_response: Inclure la réponse brute du fournisseur
        
    Returns:
        ModerationResult: Le résultat de la modération
    """
    try:
        # Pour les tests, nous traitons simplement le texte comme la transcription audio
        # En production, cette méthode traiterait le contenu comme une URL d'audio
        # ou des données binaires et utiliserait un service de modération d'audio
        
        # Simulation de modération d'audio pour les tests
        result = await moderation_service.moderate_content(
            content=content,
            moderation_type=moderation_type,
            content_type=ContentType.AUDIO,  # Indique que c'est de l'audio
            include_original_response=include_original_response
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de modération d'audio: {str(e)}")

@router.get("/moderation/{moderation_id}", response_model=ModerationResult)
async def get_moderation(moderation_id: str):
    """
    Récupère un résultat de modération par son ID.
    
    Args:
        moderation_id: L'identifiant du résultat de modération
        
    Returns:
        ModerationResult: Le résultat de modération
        
    Raises:
        HTTPException: Si le résultat n'existe pas
    """
    result = await moderation_service.get_moderation_by_id(moderation_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Résultat de modération avec ID {moderation_id} non trouvé")
    
    return result
