from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
def root() -> dict:
    docs_url = "/docs" if settings.expose_openapi else None
    return {"app_name": settings.app_name, "docs": docs_url}
