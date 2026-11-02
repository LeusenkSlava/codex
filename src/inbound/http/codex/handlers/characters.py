from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.codex.services import (
    EmotionService,
    OutfitService,
    SpriteService,
    VisualService,
)
from src.core.codex.services.emotion import EmotionMatchQuery
from src.inbound.http.codex.dependencies import (
    get_emotion_service,
    get_outfit_service,
    get_sprite_service,
    get_visual_service,
)
from src.inbound.http.codex.schemas import (
    EmotionMatchItem,
    EmotionSchema,
    EmotionTagsRequest,
    EmotionTagsResponse,
    OutfitWithEmotionsSchema,
    SpriteSchema,
    TagSchema,
    VisualsMatchRequest,
    VisualsMatchResponse,
)

router = APIRouter(tags=["characters"])


@router.get(
    "/characters/{character_id}/sprites",
    response_model=list[SpriteSchema],
    summary="Спрайты персонажа",
    description="Спрайты персонажа с тегами.",
)
async def get_sprites(
    character_id: int,
    service: Annotated[SpriteService, Depends(get_sprite_service)],
):
    return await service.get_by_character(character_id)


@router.post(
    "/characters/sprites/batch",
    response_model=dict[int, list[SpriteSchema]],
    summary="Спрайты нескольких персонажей",
    description=(
        "Спрайты для каждого `id` из списка. Ключ — `character_id`; у персонажа "
        "без спрайтов — пустой список."
    ),
)
async def get_sprites_batch(
    character_ids: list[int],
    service: Annotated[SpriteService, Depends(get_sprite_service)],
):
    return await service.get_grouped(character_ids)


@router.get(
    "/characters/{character_id}/emotions",
    response_model=list[EmotionSchema],
    summary="Эмоции персонажа",
    description="Эмоции персонажа по всем его спрайтам.",
)
async def get_emotions(
    character_id: int,
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    return await service.get_by_character(character_id)


@router.get(
    "/characters/{character_id}/emotions/tags",
    response_model=EmotionTagsResponse,
    summary="Теги эмоций персонажа",
    description=(
        "Теги эмоций персонажа по роли: `base` — базовая эмоция, "
        "`modifiers` — уточнения. Внутри групп — без повторов, по slug."
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
    summary="Подобрать эмоцию персонажа",
    description=(
        "Подбирает эмоцию по тегам. Приоритет: эмоции указанного `sprite_id`, "
        "затем больше совпавших `modifier`, затем меньше лишних `modifier`, "
        "затем меньший `id`."
    ),
    responses={404: {"description": "Подходящая эмоция не найдена."}},
)
async def match_emotion(
    character_id: int,
    payload: EmotionTagsRequest,
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    emotion = await service.match(character_id, payload.tags, payload.sprite_id)
    if emotion is None:
        raise HTTPException(status_code=404, detail="Подходящая эмоция не найдена")
    return emotion


@router.post(
    "/characters/emotions/batch",
    response_model=dict[int, EmotionSchema | None],
    summary="Подобрать эмоции персонажей",
    description=(
        "Батч-версия `POST /characters/{character_id}/emotions/match` с теми же "
        "правилами. Ключ — `character_id`, значение — `null`, если эмоция не "
        "найдена."
    ),
)
async def match_emotions_batch(
    payload: list[EmotionMatchItem],
    service: Annotated[EmotionService, Depends(get_emotion_service)],
):
    queries = [
        EmotionMatchQuery(
            character_id=item.character_id,
            tags=item.tags,
            sprite_id=item.sprite_id,
        )
        for item in payload
    ]
    return await service.match_batch(queries)


@router.get(
    "/characters/{character_id}/outfits/tags",
    response_model=list[TagSchema],
    summary="Теги одежды персонажа",
    description="Теги `outfit_style` одежды персонажа без повторов, по slug.",
)
async def get_outfit_tags(
    character_id: int,
    service: Annotated[OutfitService, Depends(get_outfit_service)],
):
    return await service.get_tags_by_character(character_id)


@router.post(
    "/characters/outfits-with-emotions/batch",
    response_model=dict[int, list[OutfitWithEmotionsSchema]],
    summary="Стили одежды с эмоциями",
    description=(
        "Для каждого персонажа — его теги `outfit_style` с `kind=base` и теги "
        "эмоций его спрайтов, к которым привязана одежда с этим тегом (сначала "
        "`base`, затем `modifier`). Ключ — `character_id`; если стилей нет — "
        "пустой список."
    ),
)
async def get_outfits_with_emotions_batch(
    character_ids: list[int],
    service: Annotated[VisualService, Depends(get_visual_service)],
):
    return await service.get_outfits_with_emotions_grouped(character_ids)


@router.post(
    "/characters/{character_id}/visuals/match",
    response_model=VisualsMatchResponse,
    summary="Подобрать визуал персонажа",
    description=(
        "Подбирает спрайт, наряд и эмоцию с одного тела. Наряд ищется по "
        "`outfit_tag` среди всех спрайтов персонажа; предпочитается спрайт, у "
        "которого есть эмоция под `emotion_tags`, затем наряд с большим `id`.\n\n"
        "Если эмоция не найдена, `emotion_asset_key` = `null`; если не найден "
        "наряд — `404`."
    ),
    responses={404: {"description": "Наряд не найден."}},
)
async def match_visuals(
    character_id: int,
    payload: VisualsMatchRequest,
    service: Annotated[VisualService, Depends(get_visual_service)],
):
    result = await service.match(character_id, payload.outfit_tag, payload.emotion_tags)
    if result is None:
        raise HTTPException(status_code=404, detail="Наряд не найден")
    return result
