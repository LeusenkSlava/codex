from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.codex.services import (
    BackgroundService,
    CharacterService,
    UniverseService,
)
from src.core.codex.services.background import BackgroundMatchQuery
from src.inbound.http.codex.dependencies import (
    get_background_service,
    get_character_service,
    get_universe_service,
)
from src.inbound.http.codex.schemas import (
    BackgroundMatchItem,
    BackgroundSchema,
    BackgroundTagsRequest,
    BackgroundTagsResponse,
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


@router.get(
    "/universes/{universe_id}/backgrounds/tags",
    response_model=BackgroundTagsResponse,
    summary="Теги задников вселенной (базовые локации и модификаторы)",
    description=(
        "Возвращает все теги задников вселенной, разделённые по роли (kind): "
        "`base` — локации, `modifiers` — уточнения (время суток, внутри/снаружи, "
        "свет, люди). Внутри каждой группы теги отсортированы по slug."
    ),
)
async def get_background_tags(
    universe_id: int,
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    return await service.get_tags_by_universe(universe_id)


@router.post(
    "/universes/{universe_id}/backgrounds/match",
    response_model=BackgroundSchema,
    summary="Подобрать задник вселенной по тегам",
    description=(
        "Подбирает один самый подходящий задник вселенной по набору тегов-смыслов.\n\n"
        "Правила подбора: тег с `kind=base` (локация) обязателен и должен быть "
        "ровно один; далее побеждает задник с большим числом совпавших `modifier`, "
        "затем — с меньшим числом лишних (неуказанных) `modifier`; при равенстве — "
        "с меньшим `id`.\n\n"
        "Если подходящий задник не найден, возвращается `404`."
    ),
    responses={404: {"description": "Подходящий задник не найден"}},
)
async def match_background(
    universe_id: int,
    payload: BackgroundTagsRequest,
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    """Подбирает один самый подходящий задник вселенной по тегам."""
    background = await service.match(universe_id, payload.tags)
    if background is None:
        raise HTTPException(status_code=404, detail="Подходящий задник не найден")
    return background


@router.post(
    "/universes/backgrounds/batch",
    response_model=dict[int, BackgroundSchema | None],
    summary="Подобрать задники для нескольких вселенных (батч)",
    description=(
        "Принимает список запросов `{universe_id, tags}` и для каждого подбирает "
        "один самый подходящий задник по тем же правилам, что и одиночный `match` "
        "(число совпавших `time_of_day`, затем меньше лишних `time_of_day`, "
        "затем меньший `id`).\n\n"
        "Ответ — словарь `universe_id -> задник`. Если ничего не подошло, "
        "значение равно `null`."
    ),
)
async def match_backgrounds_batch(
    payload: list[BackgroundMatchItem],
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    """Подбирает лучший задник для каждой вселенной из батча."""
    queries = [
        BackgroundMatchQuery(universe_id=item.universe_id, tags=item.tags)
        for item in payload
    ]
    return await service.match_batch(queries)
