# backend/app/analysis/campaign_router.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.analysis.schemas import BriefIn, AnalysisOut
from app.analysis.campaign_service import CampaignAnalysisService
from app.websearch.service import websearch_service

router = APIRouter(
    prefix="/analysis/campaign",
    tags=["campaign_analysis"],
    responses={404: {"description": "Not found"}},
)

@router.post("/analyse_campaign", response_model=AnalysisOut, summary="Analyser une campagne")
async def analyse_campaign(brief: BriefIn):
    """
    Analyser une campagne en extrayant les mots-clés, générant des résumés et effectuant des recherches web.
    
    - **campaign_name**: Nom de la campagne
    - **description**: Description de la campagne
    - **brief_items**: Liste des éléments du brief (titre et contenu)
    - **keywords_to_extract**: Nombre de mots-clés à extraire (1-30)
    - **summarize**: Générer des résumés ou non
    - **web_search**: Effectuer des recherches web ou non
    - **web_search_results_count**: Nombre de résultats de recherche web à retourner (1-10)
    
    Retourne l'analyse complète de la campagne avec les mots-clés extraits, les résumés générés et les résultats de recherche web.
    """
    campaign_service = CampaignAnalysisService(web_search_service=websearch_service)
    
    try:
        result = await campaign_service.analyze_campaign(brief)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse de la campagne: {str(e)}")
