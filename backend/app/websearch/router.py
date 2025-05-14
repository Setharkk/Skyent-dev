# backend/app/websearch/router.py
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from .service import websearch_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

@router.get("/")
async def get_websearch_status():
    return {"module": "websearch", "status": "ok"}

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Effectue une recherche web avec Tavily API.
    """
    results = await websearch_service.search(
        query=request.query,
        num_results=request.max_results
    )
    
    # Conversion en modèle Pydantic
    formatted_results = [
        SearchResult(
            title=result.get("title", ""),
            url=result.get("url", ""),
            snippet=result.get("snippet", "")
        )
        for result in results
    ]
    
    return SearchResponse(results=formatted_results)

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Effectue une recherche web avec Tavily API.
    """
    results = await websearch_service.search(
        query=request.query,
        num_results=request.max_results
    )
    
    # Conversion en modèle Pydantic
    formatted_results = [
        SearchResult(
            title=result.get("title", ""),
            url=result.get("url", ""),
            snippet=result.get("snippet", "")
        )
        for result in results
    ]
    
    return SearchResponse(results=formatted_results)
