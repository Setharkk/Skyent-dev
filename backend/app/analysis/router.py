# backend/app/analysis/router.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from .service import analysis_service

router = APIRouter()

@router.get("/")
async def get_analysis_status():
    return {"module": "analysis", "status": "ok"}

@router.post("/analyze")
async def analyze_data(data: Dict[str, Any]):
    """
    Analyse les données fournies.
    
    Args:
        data: Les données à analyser
        
    Returns:
        Dict[str, Any]: Le résultat de l'analyse
    """
    result = await analysis_service.perform_analysis(data)
    return result

@router.get("/results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """
    Récupère le résultat d'une analyse par son ID.
    
    Args:
        analysis_id: L'identifiant de l'analyse
        
    Returns:
        Dict[str, Any]: Le résultat de l'analyse
    
    Raises:
        HTTPException: Si l'analyse n'est pas trouvée
    """
    result = await analysis_service.get_analysis_by_id(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis with ID {analysis_id} not found")
    return result

@router.get("/results")
async def get_all_analysis_results():
    """
    Récupère tous les résultats d'analyse.
    
    Returns:
        List[Dict[str, Any]]: La liste des résultats d'analyse
    """
    return await analysis_service.get_all_analyses()
