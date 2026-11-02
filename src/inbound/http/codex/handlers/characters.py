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
    summary="Теги эмоций персонажа",
    description=(
        "Emotion-теги эмоций персонажа: `base` — обязательная эмоция, "
        "`modifiers` — уточнения."
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
        "Ровно один тег должен быть `base`. Приоритет: эмоции указанного "
        "`sprite_id`, затем больше совпавших `modifier`, затем меньше лишних "
        "`modifier`, затем меньший `id`. Если ничего не подошло — `404`."
    ),
    responses={404: {"description": "Подходящая эмоция не найдена"}},
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
    summary="Подобрать эмоции для нескольких персонажей (батч)",
    description=(
        "То же, что одиночный `match`, для списка персонажей. Ответ — "
        "`character_id -> эмоция` (`null`, если ничего не подошло)."
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
    description=(
        "Все outfit-теги (`outfit_style`) одежды персонажа, без повторов."
    ),
)
async def get_outfit_tags(
    character_id: int,
    service: Annotated[OutfitService, Depends(get_outfit_service)],
):
    return await service.get_tags_by_character(character_id)


@router.post(
    "/characters/outfits-with-emotions/batch",
    response_model=dict[int, list[OutfitWithEmotionsSchema]],
    summary="Теги стиля одежды и доступные для них эмоции (батч)",
    description=(
        "Для каждого персонажа — теги стиля одежды (`outfit_style`, `kind=base`) "
        "и эмоции, доступные для одежды с этим тегом (через спрайт): сначала "
        "`base`, затем `modifier`. Если тегов нет — пустой список `[]`."
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
    summary="Подобрать спрайт, наряд и эмоцию персонажа",
    description=(
        "Наряд ищется по `outfit_tag` среди всех спрайтов персонажа; "
        "предпочитается спрайт, у которого есть эмоция под `emotion_tags`, "
        "затем наряд с большим `id`.\n\n"
        "Если эмоция не найдена, `emotion_asset_key` равен `null`; если наряд "
        "не найден — `404`."
    ),
    responses={404: {"description": "Наряд не найден"}},
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
