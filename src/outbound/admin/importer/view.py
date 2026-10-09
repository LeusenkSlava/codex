from typing import Any

from sqladmin import BaseView, expose
from starlette.datastructures import UploadFile
from starlette.requests import Request

from src.outbound.admin.importer.service import ImportService
from src.outbound.database.session import async_session_factory


class ImporterView(BaseView):
    """Загрузка ZIP-архива с персонажами (дополнительный способ наполнения)."""

    name = "Импорт"
    icon = "fa-solid fa-file-import"

    @expose("/importer", methods=["GET", "POST"], identity="importer")
    async def import_page(self, request: Request) -> Any:
        context: dict[str, Any] = {
            "title": "Импорт",
            "subtitle": "Массовая загрузка персонажей из ZIP-архива",
        }

        if request.method == "POST":
            form = await request.form()
            upload = form.get("file")
            if not isinstance(upload, UploadFile) or not upload.filename:
                context["errors"] = ["Выберите ZIP-архив для импорта."]
            else:
                context["report"] = await ImportService(
                    async_session_factory
                ).import_zip(upload)

        return await self.templates.TemplateResponse(request, "importer.html", context)
