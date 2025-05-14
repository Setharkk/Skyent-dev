# backend/app/generation/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_generation_status():
    return {"module": "generation", "status": "ok"}
