from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

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
    UniverseListResponse,
    UniverseSchema,
)

router = APIRouter(tags=["universes"])


@router.get(
    "/universes",
    response_model=UniverseListResponse,
    summary="Список вселенных",
    description="Страница вселенных с обложками; поддерживает поиск по названию.",
)
async def universes_list(
    service: Annotated[UniverseService, Depends(get_universe_service)],
    search: Annotated[
        str | None,
        Query(
            description="Подстрока для поиска по `title`, без учёта регистра.",
        ),
    ] = None,
    offset: Annotated[
        int, Query(ge=0, description="Сколько вселенных пропустить.")
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Размер страницы (1..100)."),
    ] = 20,
):
    items, total = await service.search(query=search, offset=offset, limit=limit)
    return UniverseListResponse(items=items, total=total, offset=offset, limit=limit)


# FIXME: для несуществующей вселенной возвращается 500 (None не проходит
# валидацию ответа), а не 404.
@router.get(
    "/universes/{universe_id}",
    response_model=UniverseSchema,
    summary="Вселенная по id",
)
async def get_universe(
    universe_id: int,
    service: Annotated[UniverseService, Depends(get_universe_service)],
):
    return await service.get(universe_id=universe_id)


@router.get(
    "/universes/{universe_id}/characters",
    response_model=list[CharacterSchema],
    summary="Персонажи вселенной",
    description="Персонажи вселенной с тегами. Если их нет — пустой список.",
)
async def get_characters(
    universe_id: int,
    service: Annotated[CharacterService, Depends(get_character_service)],
):
    return await service.get_by_universe(universe_id)


@router.get(
    "/universes/{universe_id}/backgrounds",
    response_model=list[BackgroundSchema],
    summary="Задники вселенной",
    description="Задники вселенной с тегами и звуком (`sound_asset_key`).",
)
async def get_backgrounds(
    universe_id: int,
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    return await service.get_by_universe(universe_id)


@router.get(
    "/universes/{universe_id}/backgrounds/tags",
    response_model=BackgroundTagsResponse,
    summary="Теги задников вселенной",
    description=(
        "Теги задников вселенной по роли: `base` — локации, "
        "`modifiers` — уточнения. Внутри групп — сортировка по slug."
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
    summary="Подобрать задник вселенной",
    description=(
        "Подбирает задник по тегам. Побеждает задник с большим числом совпавших "
        "`modifier`, при равенстве — с меньшим числом лишних `modifier`, затем — "
        "с меньшим `id`."
    ),
    responses={404: {"description": "Подходящий задник не найден."}},
)
async def match_background(
    universe_id: int,
    payload: BackgroundTagsRequest,
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    background = await service.match(universe_id, payload.tags)
    if background is None:
        raise HTTPException(status_code=404, detail="Подходящий задник не найден")
    return background


@router.post(
    "/universes/backgrounds/batch",
    response_model=dict[int, BackgroundSchema | None],
    summary="Подобрать задники вселенных",
    description=(
        "Батч-версия `POST /universes/{universe_id}/backgrounds/match` с теми же "
        "правилами. Ключ — `universe_id`, значение — `null`, если задник не найден."
    ),
)
async def match_backgrounds_batch(
    payload: list[BackgroundMatchItem],
    service: Annotated[BackgroundService, Depends(get_background_service)],
):
    queries = [
        BackgroundMatchQuery(universe_id=item.universe_id, tags=item.tags)
        for item in payload
    ]
    return await service.match_batch(queries)
