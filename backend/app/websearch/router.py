# backend/app/websearch/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_websearch_status():
    return {"module": "websearch", "status": "ok"}
