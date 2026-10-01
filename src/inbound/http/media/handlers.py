from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from src.inbound.http.media.dependencies import get_media_storage
from src.main.config.settings import settings
from src.outbound.media import LocalMediaStorage

router = APIRouter()


@router.get(
    f"{settings.media.URL.rstrip('/')}/{{folder}}/{{filename}}",
    response_class=FileResponse,
    responses={
        status.HTTP_200_OK: {"content": {"image/*": {}}},
        status.HTTP_404_NOT_FOUND: {"description": "Изображение не найдено"},
    },
)
async def get_image(
    folder: str,
    filename: str,
    storage: Annotated[LocalMediaStorage, Depends(get_media_storage)],
):
    """Отдаёт изображение по asset_key (например, /media/sprites/<uuid>.png)."""
    path = storage.get_path(folder, filename)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Изображение не найдено")
    return FileResponse(path)
