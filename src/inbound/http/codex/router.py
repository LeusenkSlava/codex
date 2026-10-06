from fastapi import APIRouter

from src.inbound.http.codex.handlers import (
    characters_router,
    sprites_router,
    universes_router,
)

router = APIRouter()

router.include_router(universes_router)
router.include_router(characters_router)
router.include_router(sprites_router)
