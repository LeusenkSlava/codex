from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.codex.services import OutfitService
from src.inbound.http.codex.dependencies import get_outfit_service
from src.inbound.http.codex.schemas import OutfitSchema

router = APIRouter(tags=["sprites"])


@router.get("/sprites/{sprite_id}/outfits", response_model=list[OutfitSchema])
async def get_outfits(
    sprite_id: int,
    service: Annotated[OutfitService, Depends(get_outfit_service)],
):
    return await service.get_by_sprite(sprite_id)
