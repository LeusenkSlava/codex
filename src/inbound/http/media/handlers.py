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
        status.HTTP_200_OK: {"content": {"image/*": {}, "audio/*": {}}},
        status.HTTP_404_NOT_FOUND: {"description": "Файл не найден"},
    },
)
async def get_media_file(
    folder: str,
    filename: str,
    storage: Annotated[LocalMediaStorage, Depends(get_media_storage)],
):
    """Отдаёт медиафайл по asset_key (например, /media/sounds/<uuid>.mp3)."""
    path = storage.get_path(folder, filename)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден")
    return FileResponse(path)
