from typing import Any

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.datastructures import FormData
from starlette.requests import Request

from src.outbound.admin.views import ADMIN_VIEWS


class CodexAdmin(Admin):
    """Admin без подстановки текущего файла при редактировании."""

    @staticmethod
    async def _handle_form_data(request: Request, obj: Any = None) -> FormData:
        # sqladmin пытается восстановить файл из obj.<поле>.name (fastapi-storages),
        # а у нас файлы лежат как url-строки — пустая загрузка просто не меняет asset_key.
        return await Admin._handle_form_data(request, None)


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    """Подключает /admin к приложению."""
    admin = CodexAdmin(app, engine)
    for view in ADMIN_VIEWS:
        admin.add_view(view)
    return admin
