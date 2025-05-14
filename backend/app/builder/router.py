# backend/app/builder/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_builder_status():
    return {"module": "builder", "status": "ok"}
