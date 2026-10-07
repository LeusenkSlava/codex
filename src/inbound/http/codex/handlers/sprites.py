from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.codex.services import OutfitService
from src.inbound.http.codex.dependencies import get_outfit_service
from src.inbound.http.codex.schemas import OutfitMatchRequest, OutfitSchema

router = APIRouter(tags=["sprites"])


@router.get("/sprites/{sprite_id}/outfits", response_model=list[OutfitSchema])
async def get_outfits(
    sprite_id: int,
    service: Annotated[OutfitService, Depends(get_outfit_service)],
):
    return await service.get_by_sprite(sprite_id)


@router.post(
    "/sprites/{sprite_id}/outfits/match",
    response_model=OutfitSchema,
    summary="Подобрать одежду спрайта по тегу",
    description=(
        "Подбирает одну одежду спрайта по одному тегу-стилю.\n\n"
        "Если тегу соответствует несколько вариантов, возвращается одежда "
        "с наибольшим `id`.\n\nЕсли подходящая одежда не найдена, "
        "возвращается `404`."
    ),
    responses={404: {"description": "Подходящая одежда не найдена"}},
)
async def match_outfit(
    sprite_id: int,
    payload: OutfitMatchRequest,
    service: Annotated[OutfitService, Depends(get_outfit_service)],
):
    """Подбирает одну одежду спрайта по тегу."""
    outfit = await service.match(sprite_id, payload.tag)
    if outfit is None:
        raise HTTPException(status_code=404, detail="Подходящая одежда не найдена")
    return outfit
