from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
def root() -> dict:
    return {"app_name": settings.app_name, "docs": "/docs"}
