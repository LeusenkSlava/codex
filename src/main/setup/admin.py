from typing import Any

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.datastructures import FormData
from starlette.requests import Request

from src.outbound.admin.switcher import universe_switcher
from src.outbound.admin.views import ADMIN_TEMPLATES_DIR, ADMIN_VIEWS


class CodexAdmin(Admin):
    """Admin, который не подставляет текущий файл в поле загрузки."""

    @staticmethod
    async def _handle_form_data(request: Request, obj: Any = None) -> FormData:
        # sqladmin пытается восстановить файл из obj.<поле>.name
        # (fastapi-storages), а у нас файлы — это URL-строки: пустая загрузка
        # не должна подменять asset_key.
        return await Admin._handle_form_data(request, None)


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    """Подключает /admin к приложению."""
    admin = CodexAdmin(app, engine, templates_dir=ADMIN_TEMPLATES_DIR)
    for view in ADMIN_VIEWS:
        admin.add_view(view)
    # Переключатель вселенной доступен из общего layout каждой страницы.
    admin.templates.env.globals["universe_switcher"] = universe_switcher
    return admin
