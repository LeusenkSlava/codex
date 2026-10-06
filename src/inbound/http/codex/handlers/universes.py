from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.codex.services import (
    BackgroundService,
    CharacterService,
    UniverseService,
)
from src.inbound.http.codex.dependencies import (
    get_background_service,
    get_character_service,
    get_universe_service,
)
from src.inbound.http.codex.schemas import (
    BackgroundSchema,
    CharacterSchema,
    UniverseSchema,
)

router = APIRouter(tags=["universes"])


@router.get("/universes", response_model=list[UniverseSchema])
async def universes_list(
    service: Annotated[UniverseService, Depends(get_universe_service)],
):
    return await service.all()


# TODO Возвращает None вместо 404
@router.get("/universes/{universe_id}", response_model=UniverseSchema)
async def get_universe(
    universe_id: int,
    service: Annotated[UniverseService, Depends(get_universe_service)],
):
    return await service.get(universe_id=universe_id)


@router.get(
    "/universes/{universe_id}/characters", response_model=list[CharacterSchema]
)
async def get_characters(
    universe_id: int,
    service: Annotated[CharacterService, Depends(get_character_service)],
):
    return await service.get_by_universe(universe_id)


@router.get(
    "/universes/{universe_id}/backgrounds", response_model=list[BackgroundSchema]
)
async def get_backgrounds(
    universe_id: int,
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    return await service.get_by_universe(universe_id)
