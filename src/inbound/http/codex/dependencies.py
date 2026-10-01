from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.codex.services import (
    BackgroundService,
    CharacterService,
    EmotionService,
    OutfitService,
    SpriteService,
    UniverseService,
)
from src.outbound.database.dependencies import get_db_session
from src.outbound.database.repositories import (
    BackgroundRepository,
    CharacterRepository,
    EmotionRepository,
    OutfitRepository,
    SpriteRepository,
    UniverseRepository,
)

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_universe_service(session: SessionDep) -> UniverseService:
    return UniverseService(UniverseRepository(session))


def get_character_service(session: SessionDep) -> CharacterService:
    return CharacterService(CharacterRepository(session))


def get_sprite_service(session: SessionDep) -> SpriteService:
    return SpriteService(SpriteRepository(session))


def get_emotion_service(session: SessionDep) -> EmotionService:
    return EmotionService(EmotionRepository(session))


def get_outfit_service(session: SessionDep) -> OutfitService:
    return OutfitService(OutfitRepository(session))


def get_background_service(session: SessionDep) -> BackgroundService:
    return BackgroundService(BackgroundRepository(session))
