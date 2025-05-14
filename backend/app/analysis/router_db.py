# backend/app/analysis/router_db.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from .service_db import AnalysisDBService
from .schemas import ContentAnalysisRequest, ContentAnalysisResponse

router = APIRouter()

@router.get("/db")
async def get_analysis_db_status():
    """Vérifier le statut du module d'analyse avec base de données."""
    return {"module": "analysis_db", "status": "ok"}

@router.post("/db/analyze", response_model=ContentAnalysisResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Analyser un contenu et stocker les résultats en base de données.
    
    Args:
        request: La requête contenant le contenu à analyser et les options
        session: La session de base de données (injectée par FastAPI)
    
    Returns:
        ContentAnalysisResponse: Le résultat de l'analyse
    """
    service = AnalysisDBService(session)
    
    try:
        result = await service.analyze_content(
            content=request.content,
            analyze_sentiment=request.analyze_sentiment,
            extract_keywords=request.extract_keywords,
            create_summary=request.create_summary
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse du contenu: {str(e)}"
        )

@router.get("/db/results/{analysis_id}")
async def get_analysis_by_id(
    analysis_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Récupérer une analyse par son ID.
    
    Args:
        analysis_id: L'ID de l'analyse
        session: La session de base de données (injectée par FastAPI)
    
    Returns:
        Analysis: L'analyse demandée
    
    Raises:
        HTTPException: Si l'analyse n'est pas trouvée
    """
    service = AnalysisDBService(session)
    
    result = await service.get_analysis_by_id(analysis_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analyse avec l'ID {analysis_id} non trouvée"
        )
    
    return result

@router.get("/db/results")
async def list_analyses(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Lister toutes les analyses avec pagination.
    
    Args:
        skip: Le nombre d'éléments à sauter
        limit: Le nombre maximal d'éléments à retourner
        session: La session de base de données (injectée par FastAPI)
    
    Returns:
        List[Analysis]: La liste des analyses
    """
    service = AnalysisDBService(session)
    
    return await service.list_analyses(skip, limit)