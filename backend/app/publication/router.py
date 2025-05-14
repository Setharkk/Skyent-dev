# backend/app/publication/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_publication_status():
    return {"module": "publication", "status": "ok"}
