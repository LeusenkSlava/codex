from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.codex.services import (
    BackgroundService,
    CharacterService,
    EmotionService,
    OutfitService,
    SpriteService,
    UniverseService,
)
from src.inbound.http.codex.dependencies import (
    get_background_service,
    get_character_service,
    get_emotion_service,
    get_outfit_service,
    get_sprite_service,
    get_universe_service,
)
from src.inbound.http.codex.schemas import (
    BackgroundSchema,
    CharacterSchema,
    EmotionSchema,
    OutfitSchema,
    SpriteSchema,
    UniverseSchema,
)

router = APIRouter()


@router.get("/universes", response_model=list[UniverseSchema])
async def get_universes(
    service: Annotated[UniverseService, Depends(get_universe_service)],
):
    return await service.get_all()


@router.get("/universes/{universe_id}/characters", response_model=list[CharacterSchema])
async def get_characters(
    universe_id: int,
    service: Annotated[CharacterService, Depends(get_character_service)],
):
    return await service.get_by_universe(universe_id)


@router.get("/universes/{universe_id}/backgrounds", response_model=list[BackgroundSchema])
async def get_backgrounds(
    universe_id: int,
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    return await service.get_by_universe(universe_id)


@router.get("/characters/{character_id}/sprites", response_model=list[SpriteSchema])
async def get_sprites(
    character_id: int,
    service: Annotated[SpriteService, Depends(get_sprite_service)],
):
    return await service.get_by_character(character_id)


@router.get("/characters/{character_id}/emotions", response_model=list[EmotionSchema])
async def get_emotions(
    character_id: int,
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    return await service.get_by_character(character_id)


@router.get("/sprites/{sprite_id}/outfits", response_model=list[OutfitSchema])
async def get_outfits(
    sprite_id: int,
    service: Annotated[OutfitService, Depends(get_outfit_service)],
):
    return await service.get_by_sprite(sprite_id)
