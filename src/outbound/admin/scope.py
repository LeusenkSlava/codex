"""Скоп админки по вселенной.

Активная вселенная хранится в cookie ``codex_universe_id`` (её ставит
переключатель в шапке админки). От неё зависят списки записей и
FK-селекторы у персонажей, спрайтов, одежды, эмоций, фонов и звуков.

Связи: ``Universe -> Character -> Sprite -> Outfit/Emotion`` и
``Universe -> Background/Sound``. Теги остаются глобальными.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from sqlalchemy import Select, true
from sqlalchemy.sql.elements import ColumnElement
from starlette.requests import Request

from src.outbound.database.models.character import (
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
)
from src.outbound.database.models.universe import BackgroundModel, SoundModel

UNIVERSE_COOKIE = "codex_universe_id"

# Активная вселенная текущего запроса — нужна там, где нет Request
# (например, в scaffold_form при построении формы создания).
_active_universe: ContextVar[int | None] = ContextVar(
    "codex_active_universe", default=None
)

# Сам запрос — тоже нужен в scaffold_form: по path-параметру ``pk`` можно
# понять, что это форма редактирования, и сохранить текущую связь в списке
# вариантов, даже если объект не попал в скоп выбранной вселенной.
_active_request: ContextVar[Request | None] = ContextVar(
    "codex_active_request", default=None
)

# Сущности с прямой колонкой universe_id.
_DIRECT = (CharacterModel, BackgroundModel, SoundModel)


def parse_universe_id(raw: str | None) -> int | None:
    """Разобрать id вселенной из cookie/формы; пустое значение = без скопа."""
    if raw in (None, "", "__all__"):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def get_active_universe_id(request: Request) -> int | None:
    return parse_universe_id(request.cookies.get(UNIVERSE_COOKIE))


def current_universe_id() -> int | None:
    """Активная вселенная текущего запроса (для кода без Request)."""
    return _active_universe.get()


def current_request() -> Request | None:
    """Текущий HTTP-запрос (для кода без Request, например scaffold_form)."""
    return _active_request.get()


class UniverseScopeMiddleware:
    """Прокидывает активную вселенную из cookie в contextvar на время запроса.

    Нужен, чтобы ``scaffold_form`` (у него нет Request) мог подставить
    вселенную по умолчанию в форму создания и отфильтровать варианты
    FK-селекторов.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        universe_token = _active_universe.set(get_active_universe_id(request))
        request_token = _active_request.set(request)
        try:
            await self.app(scope, receive, send)
        finally:
            _active_request.reset(request_token)
            _active_universe.reset(universe_token)


def scope_where(model: Any, universe_id: int | None) -> ColumnElement:
    """Предикат, оставляющий у ``model`` только записи выбранной вселенной.

    При ``universe_id is None`` возвращает ``true()`` — селекторы и списки
    тогда показывают всё (режим «Все вселенные»).
    """
    if universe_id is None:
        return true()

    if model is CharacterModel or model is BackgroundModel or model is SoundModel:
        return model.universe_id == universe_id

    if model is SpriteModel:
        return SpriteModel.character.has(CharacterModel.universe_id == universe_id)

    if model is OutfitModel or model is EmotionModel:
        return model.sprite.has(
            SpriteModel.character.has(CharacterModel.universe_id == universe_id)
        )

    # Universe/Tag и прочие не привязаны к вселенной — не скопируем.
    return true()


def scope_list_query(query: Select, model: Any, universe_id: int | None) -> Select:
    return query.where(scope_where(model, universe_id))
