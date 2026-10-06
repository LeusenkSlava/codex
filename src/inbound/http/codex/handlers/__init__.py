from src.inbound.http.codex.handlers.characters import router as characters_router
from src.inbound.http.codex.handlers.sprites import router as sprites_router
from src.inbound.http.codex.handlers.universes import router as universes_router

__all__ = ["characters_router", "sprites_router", "universes_router"]
