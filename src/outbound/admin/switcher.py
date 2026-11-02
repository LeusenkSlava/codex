"""Переключатель активной вселенной в шапке админки.

Состоит из двух частей:

- ``UniverseScopeView`` — служебный POST-маршрут, который ставит/снимает
  cookie ``codex_universe_id`` и редиректит обратно на текущую страницу;
- ``universe_switcher`` — async Jinja-global, отрисовывающий сам селектор
  (список вселенных + активная) в общий layout.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from jinja2 import pass_context
from markupsafe import Markup, escape
from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.outbound.admin.scope import (
    UNIVERSE_COOKIE,
    get_active_universe_id,
    parse_universe_id,
)
from src.outbound.database.models.universe import UniverseModel
from src.outbound.database.session import async_session_factory

_COOKIE_PATH = "/"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 дней
# Параметры, которые имеет смысл сохранить при смене вселенной. Фильтры по
# спрайтам/персонажам (…_id) и страница сбрасываются: они относятся к прежней
# вселенной и дали бы пустую выборку.
_KEEP_QUERY = {"search", "sort", "sortBy"}


class UniverseScopeView(BaseView):
    """Маршрут установки активной вселенной. В меню не показывается."""

    name = "Переключение вселенной"
    icon = "fa-solid fa-globe"

    @expose("/universe-scope/set", methods=["POST"], identity="universe-scope")
    async def set_universe(self, request: Request) -> RedirectResponse:
        form = await request.form()
        universe_id = parse_universe_id(form.get("universe_id", ""))

        next_path = form.get("next") or ""
        if not next_path.startswith("/"):
            next_path = str(request.url_for("admin:index"))

        response = RedirectResponse(next_path, status_code=302)
        if universe_id is None:
            response.delete_cookie(UNIVERSE_COOKIE, path=_COOKIE_PATH)
        else:
            response.set_cookie(
                UNIVERSE_COOKIE,
                str(universe_id),
                path=_COOKIE_PATH,
                max_age=_COOKIE_MAX_AGE,
                httponly=True,
                samesite="lax",
            )
        return response

    def is_visible(self, request: Request) -> bool:
        return False


@pass_context
async def universe_switcher(context: dict[str, Any]) -> Markup:
    """Отрисовать селектор вселенной (вызывается из layout.html)."""
    request: Request = context["request"]
    active_id = get_active_universe_id(request)

    async with async_session_factory() as session:
        universes = (
            await session.scalars(select(UniverseModel).order_by(UniverseModel.title))
        ).all()

    set_url = request.url_for("admin:view-universe-scope")
    params = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key in _KEEP_QUERY
    ]
    query = urlencode(params)
    next_path = request.url.path + (f"?{query}" if query else "")

    options = ['<option value="__all__">Все вселенные</option>']
    for universe in universes:
        selected = " selected" if universe.id == active_id else ""
        options.append(
            f'<option value="{universe.id}"{selected}>{escape(universe.title)}</option>'
        )

    # Собираем строку до Markup: Markup.format() экранировал бы теги <option>.
    return Markup(
        f'<form method="post" action="{escape(set_url)}" class="universe-switcher">'
        f'<input type="hidden" name="next" value="{escape(next_path)}">'
        '<label class="form-label text-light small mb-1 d-block">Вселенная</label>'
        '<select name="universe_id" class="form-select form-select-sm" '
        f'onchange="this.form.submit()">{"".join(options)}</select>'
        "</form>"
    )
