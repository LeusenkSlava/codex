from typing import Any, ClassVar

from markupsafe import Markup
from sqlalchemy import select
from starlette.datastructures import UploadFile
from starlette.requests import Request
from wtforms import FileField, Form

from src.core.codex.models.enum import TagType
from src.outbound.database.models.character import (
    EmotionModel,
    OutfitModel,
    SpriteModel,
)
from src.outbound.database.models.tag import TagModel
from src.outbound.database.models.universe import BackgroundModel, SoundModel
from src.outbound.media import media_storage


def _image_preview(model: Any, _attr: Any) -> Markup:
    if not model.asset_key:
        return Markup("")
    return Markup('<img src="{}" style="max-height: 80px">').format(model.asset_key)


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
    """Загрузка медиафайла вместо ручного ввода asset_key.

    Файл сохраняется в папку медиа, в asset_key пишется его url.
    """

    asset_folder: ClassVar[str]
    asset_label: ClassVar[str] = "Изображение"
    asset_field = "file"

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
            old_url = None if is_created else model.asset_key
            data["asset_key"] = await media_storage.save(upload, self.asset_folder)
            media_storage.delete(old_url)
        elif is_created:
            raise ValueError("Загрузите изображение")

    async def after_model_delete(self, model: Any, request: Request) -> None:
        media_storage.delete(model.asset_key)


class TagTypeFilterMixin:
    """Показывает в выборе тегов только теги указанных типов."""

    tag_types: ClassVar[tuple[TagType, ...]]

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        stmt = (
            select(TagModel)
            .where(TagModel.type.in_(self.tag_types))
            .order_by(TagModel.name)
        )
        async with self.session_maker() as session:  # type: ignore[attr-defined]
            tags = (await session.scalars(stmt)).all()
        # опции считаются при каждом построении формы, чтобы подхватывать новые теги
        self.form_args = {
            **self.form_args,  # type: ignore[has-type]
            "tags": {"data": [(str(tag.id), tag.name) for tag in tags]},
        }
        return await super().scaffold_form(rules)  # type: ignore[misc]


class MediaCleanupMixin:
    """Чистит файлы записей, удалённых каскадом вместе с этой.

    Например, при удалении спрайта БД удаляет его одежду и эмоции,
    а их картинки остаются на диске — убираем всё, на что нет ссылок.
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
        media_storage.delete_unreferenced(referenced)
