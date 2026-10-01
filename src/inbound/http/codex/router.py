from fastapi import APIRouter

from src.inbound.http.codex.handlers import router as handlers_router

router = APIRouter()

router.include_router(handlers_router, tags=["codex"])
