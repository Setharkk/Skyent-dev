# backend/app/model_selector/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_model_selector_status():
    return {"module": "model_selector", "status": "ok"}
