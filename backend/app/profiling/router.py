# backend/app/profiling/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_profiling_status():
    return {"module": "profiling", "status": "ok"}
