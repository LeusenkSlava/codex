"""Кастомные фильтры для списков админки."""

from typing import Any

from sqlalchemy import Select, select
from sqladmin.filters import get_parameter_name, get_title
from starlette.requests import Request

from src.core.codex.models.enum import TagType
from src.outbound.database.models.tag import TagModel


class TagFilter:
    """Фильтр списка по тегу (M2M-связь ``tags``).

    Показывает в выпадающем списке теги указанных типов (``None`` — все типы)
    и оставляет в выборке только объекты, у которых есть выбранный тег.
    """

    has_operator = False
    template = "sqladmin/filters/lookup_filter.html"

    def __init__(
        self,
        tag_types: tuple[TagType, ...] | None = None,
        *,
        title: str = "Тег",
        parameter_name: str = "tag_id",
    ) -> None:
        self.tag_types = tuple(tag_types) if tag_types else None
        self.title = title
        self.parameter_name = parameter_name

    async def lookups(
        self,
        request: Request,
        model: Any,
        run_query: Any,
    ) -> list[tuple[str, str]]:
        stmt = select(TagModel.id, TagModel.name)
        if self.tag_types:
            stmt = stmt.where(TagModel.type.in_(self.tag_types))
        stmt = stmt.order_by(TagModel.name)
        return [("__all", "All")] + [
            (str(tag_id), name) for tag_id, name in await run_query(stmt)
        ]

    async def get_filtered_query(
        self, query: Select, value: Any, model: Any
    ) -> Select:
        if value in ("", "__all", None):
            return query
        try:
            tag_id = int(value)
        except (TypeError, ValueError):
            return query
        return query.where(getattr(model, "tags").any(TagModel.id == tag_id))


class ForeignKeyObjectFilter:
    """FK-фильтр, показывающий в выпадающем списке ``str()`` связанного объекта.

    Удобнее встроенного ``ForeignKeyFilter``, когда у связанной модели есть
    осмысленный ``__str__`` (например, спрайт — «Имя персонажа / slug»),
    а не один-единственный столбец.
    """

    has_operator = False
    template = "sqladmin/filters/lookup_filter.html"

    def __init__(
        self,
        foreign_key: Any,
        foreign_model: Any,
        *,
        title: str | None = None,
        parameter_name: str | None = None,
    ) -> None:
        self.foreign_key = foreign_key
        self.foreign_model = foreign_model
        self.title = title or get_title(foreign_key)
        self.parameter_name = parameter_name or get_parameter_name(foreign_key)

    async def lookups(
        self,
        request: Request,
        model: Any,
        run_query: Any,
    ) -> list[tuple[str, str]]:
        rows = await run_query(select(self.foreign_model).distinct())
        return [("__all", "All")] + [
            (str(obj.id), str(obj)) for (obj,) in rows
        ]

    async def get_filtered_query(
        self, query: Select, value: Any, model: Any
    ) -> Select:
        if value in ("", "__all", None):
            return query
        try:
            value = int(value)
        except (TypeError, ValueError):
            return query
        return query.filter(self.foreign_key == value)
