from pathlib import Path
from typing import Any, ClassVar

from markupsafe import Markup
from sqlalchemy import Select, inspect as sqlalchemy_inspect, or_, select
from starlette.datastructures import UploadFile
from starlette.requests import Request
from wtforms import FileField, Form

from src.core.codex.models.enum import TagType
from src.outbound.admin.scope import (
    current_request,
    current_universe_id,
    get_active_universe_id,
    scope_list_query,
    scope_where,
)
from src.outbound.database.models.character import (
    EmotionModel,
    OutfitModel,
    SpriteModel,
)
from src.outbound.database.models.tag import TagModel
from src.outbound.database.models.universe import (
    BackgroundModel,
    SoundModel,
    UniverseModel,
)
from src.outbound.media import media_storage


def _image_preview(model: Any, attr: Any) -> Markup:
    # sqladmin передаёт в форматтер имя свойства: картинкой может быть любое
    # поле-URL, поэтому сначала пробуем attr, затем asset_key.
    url = getattr(model, attr, None) if isinstance(attr, str) else None
    if not url:
        url = getattr(model, "asset_key", None)
    if not url:
        return Markup("")
    return Markup('<img src="{}" style="max-height: 80px">').format(url)


def _audio_preview(model: Any, _attr: Any) -> Markup:
    if not model.asset_key:
        return Markup("")
    return Markup(
        '<audio controls preload="none" src="{}" style="max-height: 40px"></audio>'
    ).format(model.asset_key)


_TAG_TYPE_BADGE: dict[TagType, str] = {
    TagType.EMOTION: "bg-red text-white",
    TagType.OUTFIT_STYLE: "bg-blue text-white",
    TagType.LOCATION: "bg-green text-white",
    TagType.TIME_OF_DAY: "bg-yellow text-dark",
    TagType.ARCHETYPE: "bg-purple text-white",
    TagType.MUSIC: "bg-cyan text-white",
    TagType.SFX: "bg-orange text-white",
}


def _tags_formatter(model: Any, _attr: Any) -> list[Markup]:
    tags = sorted(getattr(model, "tags", None) or (), key=lambda tag: tag.name)
    return [
        Markup(
            f'<span class="badge {_TAG_TYPE_BADGE.get(tag.type, "bg-secondary text-light")}" '
            f'title="{tag.type.value}">{Markup.escape(tag.name)}</span>'
        )
        for tag in tags
    ]


class AssetUploadMixin:
    """Загрузка файла вместо ручного ввода URL ассета.

    Файл сохраняется в папку `asset_folder`, а его URL записывается в поле
    `asset_attribute` (по умолчанию `asset_key`; у вселенной —
    `cover_asset_key`). При замене и удалении записи старый файл удаляется.
    """

    asset_folder: ClassVar[str]
    asset_attribute: ClassVar[str] = "asset_key"
    asset_required: ClassVar[bool] = True
    asset_label: ClassVar[str] = "Изображение"
    asset_field: ClassVar[str] = "file"
    # необязательный фильтр расширений (например, только картинки)
    asset_extensions: ClassVar[frozenset[str] | None] = None

    column_formatters: ClassVar[dict] = {
        "asset_key": _image_preview,
        "tags": _tags_formatter,
    }
    column_formatters_detail: ClassVar[dict] = {
        "asset_key": _image_preview,
        "tags": _tags_formatter,
    }

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        form = await super().scaffold_form(rules)  # type: ignore[misc]

        class AssetForm(form):  # type: ignore[valid-type, misc]
            pass

        setattr(
            AssetForm,
            self.asset_field,
            FileField(
                self.asset_label,
                description="При редактировании оставьте пустым, чтобы не менять файл.",
            ),
        )
        return AssetForm

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        upload = data.pop(self.asset_field, None)
        if isinstance(upload, UploadFile) and upload.filename:
            ext = Path(upload.filename).suffix.lower()
            if self.asset_extensions is not None and ext not in self.asset_extensions:
                raise ValueError(
                    f"Недопустимый формат файла {ext!r}, разрешены: "
                    f"{', '.join(sorted(self.asset_extensions))}"
                )
            old_url = (
                None if is_created else getattr(model, self.asset_attribute, None)
            )
            data[self.asset_attribute] = await media_storage.save(
                upload, self.asset_folder
            )
            media_storage.delete(old_url)
        elif is_created and self.asset_required:
            raise ValueError(f"Загрузите {self.asset_label.lower()}")

    async def after_model_delete(self, model: Any, request: Request) -> None:
        # Файл удаляется до super(): следующий миксин собирает ссылки из БД,
        # а этого файла там уже быть не должно — иначе он останется сиротой.
        media_storage.delete(getattr(model, self.asset_attribute, None))
        await super().after_model_delete(model, request)  # type: ignore[misc]


def _current_edit_pk() -> int | None:
    """id редактируемой записи из пути ``.../edit/{pk}`` (иначе ``None``)."""
    request = current_request()
    if request is None:
        return None
    try:
        return int(request.path_params["pk"])
    except (KeyError, TypeError, ValueError):
        return None


class UniverseScopedMixin:
    """Ограничивает список записей активной вселенной (переключатель в шапке).

    Наследуется вьюхами сущностей, привязанных к вселенной напрямую или
    через цепочку персонаж -> спрайт. Сами вселенные и теги не скопируются.

    Поля из ``scoped_relation_fields`` (MANYTOONE-связи) тоже наполняются
    вариантами выбранной вселенной. Это обычный ``<select>`` со всеми
    вариантами сразу — поиск по нему необязателен (его делает select2 на
    клиенте), в отличие от ``form_ajax_refs``, где без ввода символов
    список оставался пустым.
    """

    # Имя поля-вселенной во форме: если задано, при создании оно
    # подставляется из активной вселенной (например, "universe").
    universe_default_field: ClassVar[str | None] = None
    # MANYTOONE-связи, варианты которых ограничиваем активной вселенной.
    scoped_relation_fields: ClassVar[tuple[str, ...]] = ()

    def list_query(self, request: Request) -> Select:
        stmt = super().list_query(request)  # type: ignore[misc]
        universe_id = get_active_universe_id(request)
        if universe_id is not None:
            stmt = scope_list_query(stmt, self.model, universe_id)  # type: ignore[attr-defined]
        return stmt

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        # Экземпляр вьюхи переиспользуется между запросами, поэтому берём
        # копию form_args и пересобираем динамические поля каждый раз —
        # иначе значения залипали бы после смены вселенной.
        form_args = dict(self.form_args)  # type: ignore[attr-defined]
        universe_id = current_universe_id()

        if self.universe_default_field:
            # default применяется только к пустой форме (создание); при
            # редактировании sqladmin подставляет данные объекта, и они
            # побеждают default.
            class_args = type(self).form_args  # type: ignore[attr-defined]
            field_args = dict(class_args.get(self.universe_default_field, {}))
            if universe_id is not None:
                field_args["default"] = str(universe_id)
            else:
                field_args.pop("default", None)
            form_args[self.universe_default_field] = field_args

        for field_name in self.scoped_relation_fields:
            field_args = dict(form_args.get(field_name, {}))
            field_args["data"] = await self._scoped_relation_choices(field_name)
            # data-role подхватывает layout.html: select2 с локальными
            # вариантами и необязательным поиском по подстроке.
            field_args["render_kw"] = {
                **field_args.get("render_kw", {}),
                "class": "form-control",
                "data-role": "select2-local",
                "data-placeholder": "Не выбрано",
            }
            field_args["description"] = (
                "Показаны объекты выбранной вселенной; поиск необязателен."
            )
            form_args[field_name] = field_args

        self.form_args = form_args  # type: ignore[assignment]
        return await super().scaffold_form(rules)  # type: ignore[misc]

    async def _scoped_relation_choices(self, field_name: str) -> list[tuple[str, str]]:
        """Варианты FK-поля: объекты выбранной вселенной + текущая связь."""
        mapper = sqlalchemy_inspect(self.model)  # type: ignore[attr-defined]
        relation = mapper.relationships[field_name]
        target = relation.mapper.class_
        stmt = select(target)
        scope = scope_where(target, current_universe_id())

        edit_pk = _current_edit_pk()
        if edit_pk is not None and len(relation.local_columns) == 1:
            # При редактировании текущая связь должна остаться в списке,
            # даже если объект не попал в скоп (например, после смены
            # вселенной) — иначе сохранение молча переписало бы её.
            fk_column = next(iter(relation.local_columns))
            current_fk = select(fk_column).where(
                self.model.id == edit_pk  # type: ignore[attr-defined]
            )
            stmt = stmt.where(or_(scope, target.id.in_(current_fk)))
        else:
            stmt = stmt.where(scope)

        async with self.session_maker() as session:  # type: ignore[attr-defined]
            objects = (await session.scalars(stmt)).unique().all()

        choices = {str(obj.id): str(obj) for obj in objects}
        return sorted(choices.items(), key=lambda item: item[1].casefold())


class TagTypeFilterMixin:
    """Оставляет в поле `tags` формы только теги типов `tag_types`."""

    tag_types: ClassVar[tuple[TagType, ...]]

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        stmt = (
            select(TagModel)
            .where(TagModel.type.in_(self.tag_types))
            .order_by(TagModel.name)
        )
        async with self.session_maker() as session:  # type: ignore[attr-defined]
            tags = (await session.scalars(stmt)).all()
        # Опции пересобираются при каждом построении формы, чтобы новые теги
        # сразу появлялись в выборе.
        self.form_args = {
            **self.form_args,  # type: ignore[has-type]
            "tags": {"data": [(str(tag.id), tag.name) for tag in tags]},
        }
        return await super().scaffold_form(rules)  # type: ignore[misc]


class MediaCleanupMixin:
    """Удаляет файлы ассетов, удалённых каскадом вместе с этой записью.

    Например, при удалении спрайта БД удаляет его одежду и эмоции, а их
    картинки остались бы на диске. После удаления в медиа остаются только
    файлы, на которые ещё есть ссылки, включая обложки вселенных.
    """

    async def after_model_delete(self, model: Any, request: Request) -> None:
        referenced: set[str] = set()
        async with self.session_maker() as session:  # type: ignore[attr-defined]
            for asset_model in (
                SpriteModel,
                OutfitModel,
                EmotionModel,
                BackgroundModel,
                SoundModel,
            ):
                referenced.update(await session.scalars(select(asset_model.asset_key)))
            # Обложки лежат в медиа как и ассеты: без них cleanup снёс бы их
            # при любом удалении через админку.
            covers = await session.scalars(select(UniverseModel.cover_asset_key))
            referenced.update(cover for cover in covers if cover)
        media_storage.delete_unreferenced(referenced)
