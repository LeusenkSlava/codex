from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.codex.services import EmotionService, SpriteService
from src.core.codex.services.emotion import EmotionMatchQuery
from src.inbound.http.codex.dependencies import (
    get_emotion_service,
    get_sprite_service,
)
from src.inbound.http.codex.schemas import (
    EmotionMatchItem,
    EmotionSchema,
    EmotionTagsRequest,
    EmotionTagsResponse,
    SpriteSchema,
)

router = APIRouter(tags=["characters"])


@router.get("/characters/{character_id}/sprites", response_model=list[SpriteSchema])
async def get_sprites(
    character_id: int,
    service: Annotated[SpriteService, Depends(get_sprite_service)],
):
    return await service.get_by_character(character_id)


@router.post("/characters/sprites/batch", response_model=dict[int, list[SpriteSchema]])
async def get_sprites_batch(
    character_ids: list[int],
    service: Annotated[SpriteService, Depends(get_sprite_service)],
):
    return await service.get_grouped(character_ids)


@router.get("/characters/{character_id}/emotions", response_model=list[EmotionSchema])
async def get_emotions(
    character_id: int,
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    return await service.get_by_character(character_id)


@router.get(
    "/characters/{character_id}/emotions/tags",
    response_model=EmotionTagsResponse,
    summary="Теги эмоций персонажа (базовые и модификаторы)",
    description=(
        "Возвращает все emotion-теги, которые встречаются у эмоций персонажа, "
        "разделённые на два списка: `base` (обязательная эмоция) и "
        "`modifiers` (уточнения)."
    ),
)
async def get_emotion_tags(
    character_id: int,
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    return await service.get_tags_by_character(character_id)


@router.post(
    "/characters/{character_id}/emotions/match",
    response_model=EmotionSchema,
    summary="Подобрать эмоцию персонажа по тегам",
    description=(
        "Подбирает одну самую подходящую эмоцию персонажа по набору тегов-смыслов.\n\n"
        "Правила подбора: тег с `kind=base` обязателен и должен быть ровно один; "
        "если передан `sprite_id`, эмоции этого спрайта приоритетнее; далее побеждает "
        "эмоция с большим числом совпавших `modifier`, затем — с меньшим числом лишних "
        "(неуказанных) `modifier`; при равенстве — с меньшим `id`.\n\n"
        "Если подходящая эмоция не найдена, возвращается `404`."
    ),
    responses={404: {"description": "Подходящая эмоция не найдена"}},
)
async def match_emotion(
    character_id: int,
    payload: EmotionTagsRequest,
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    """Подбирает одну самую подходящую эмоцию персонажа по тегам."""
    emotion = await service.match(character_id, payload.tags, payload.sprite_id)
    if emotion is None:
        raise HTTPException(status_code=404, detail="Подходящая эмоция не найдена")
    return emotion


@router.post(
    "/characters/emotions/batch",
    response_model=dict[int, EmotionSchema | None],
    summary="Подобрать эмоции для нескольких персонажей (батч)",
    description=(
        "Принимает список запросов `{character_id, tags, sprite_id?}` и для каждого "
        "подбирает одну самую подходящую эмоцию по тем же правилам, что и одиночный "
        "`match` (приоритет спрайта, затем число совпавших `modifier`, затем меньше "
        "лишних `modifier`).\n\n"
        "Ответ — словарь `character_id -> эмоция`. Если для персонажа ничего не подошло, "
        "значение равно `null`."
    ),
)
async def match_emotions_batch(
    payload: list[EmotionMatchItem],
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    """Подбирает лучшую эмоцию для каждого персонажа из батча."""
    queries = [
        EmotionMatchQuery(
            character_id=item.character_id,
            tags=item.tags,
            sprite_id=item.sprite_id,
        )
        for item in payload
    ]
    return await service.match_batch(queries)
