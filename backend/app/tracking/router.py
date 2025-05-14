# backend/app/tracking/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_tracking_status():
    return {"module": "tracking", "status": "ok"}
