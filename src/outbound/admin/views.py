from typing import Any, ClassVar

from markupsafe import Markup
from sqladmin import ModelView
from sqladmin.filters import AllUniqueStringValuesFilter
from sqlalchemy import select
from starlette.datastructures import UploadFile
from starlette.requests import Request
from wtforms import FileField, Form

from src.core.codex.models.enum import TagType
from src.outbound.database.models.character import (
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
)
from src.outbound.database.models.tag import TagModel
from src.outbound.database.models.universe import BackgroundModel, UniverseModel
from src.outbound.media import media_storage


def _image_preview(model: Any, _attr: Any) -> Markup:
    if not model.asset_key:
        return Markup("")
    return Markup('<img src="{}" style="max-height: 80px">').format(model.asset_key)


class AssetUploadMixin:
    """Загрузка картинки вместо ручного ввода asset_key.

    Файл сохраняется в папку медиа, в asset_key пишется его url.
    """

    asset_folder: ClassVar[str]
    asset_field = "file"

    column_formatters: ClassVar[dict] = {"asset_key": _image_preview}
    column_formatters_detail: ClassVar[dict] = {"asset_key": _image_preview}

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        form = await super().scaffold_form(rules)  # type: ignore[misc]

        class AssetForm(form):  # type: ignore[valid-type, misc]
            pass

        setattr(
            AssetForm,
            self.asset_field,
            FileField(
                "Изображение",
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
            ):
                referenced.update(await session.scalars(select(asset_model.asset_key)))
        media_storage.delete_unreferenced(referenced)


class UniverseAdmin(MediaCleanupMixin, ModelView, model=UniverseModel):
    column_list = [UniverseModel.id, UniverseModel.slug, UniverseModel.title]
    column_searchable_list = [UniverseModel.slug, UniverseModel.title]
    form_columns = [
        UniverseModel.slug,
        UniverseModel.title,
        UniverseModel.description,
    ]
    name_plural = "Вселенные"
    icon = "fa-solid fa-globe"


class CharacterAdmin(MediaCleanupMixin, ModelView, model=CharacterModel):
    column_list = [
        CharacterModel.id,
        CharacterModel.universe_id,
        CharacterModel.slug,
        CharacterModel.name,
    ]
    column_searchable_list = [CharacterModel.slug, CharacterModel.name]
    # tags - M2M, sqladmin отрисует как multi-select по уже созданным TagModel
    form_columns = [
        CharacterModel.universe,
        CharacterModel.slug,
        CharacterModel.name,
        CharacterModel.description,
        CharacterModel.speech_style,
        CharacterModel.tags,
    ]
    name_plural = "Персонажи"
    icon = "fa-solid fa-user"


class SpriteAdmin(MediaCleanupMixin, AssetUploadMixin, ModelView, model=SpriteModel):
    asset_folder = "sprites"
    column_list = [
        SpriteModel.id,
        SpriteModel.character_id,
        SpriteModel.slug,
        SpriteModel.asset_key,
    ]
    form_columns = [
        SpriteModel.character,
        SpriteModel.slug,
        SpriteModel.description,
        SpriteModel.tags,
    ]
    name_plural = "Спрайты"
    icon = "fa-solid fa-image"


class OutfitAdmin(TagTypeFilterMixin, AssetUploadMixin, ModelView, model=OutfitModel):
    tag_types = (TagType.OUTFIT_STYLE,)
    asset_folder = "outfits"
    column_list = [
        OutfitModel.id,
        OutfitModel.sprite,
        OutfitModel.slug,
        OutfitModel.name,
        OutfitModel.asset_key,
    ]
    column_searchable_list = [OutfitModel.slug, OutfitModel.name]
    form_columns = [
        OutfitModel.sprite,
        OutfitModel.slug,
        OutfitModel.name,
        OutfitModel.tags,
    ]
    name_plural = "Одежда"
    icon = "fa-solid fa-shirt"


class EmotionAdmin(TagTypeFilterMixin, AssetUploadMixin, ModelView, model=EmotionModel):
    tag_types = (TagType.EMOTION,)
    asset_folder = "emotions"
    column_list = [
        EmotionModel.id,
        EmotionModel.sprite,
        EmotionModel.slug,
        EmotionModel.name,
        EmotionModel.asset_key,
    ]
    column_searchable_list = [EmotionModel.slug, EmotionModel.name]
    form_columns = [
        EmotionModel.sprite,
        EmotionModel.slug,
        EmotionModel.name,
        EmotionModel.tags,
    ]
    name_plural = "Эмоции"
    icon = "fa-solid fa-face-smile"


class BackgroundAdmin(
    TagTypeFilterMixin, AssetUploadMixin, ModelView, model=BackgroundModel
):
    tag_types = (TagType.LOCATION, TagType.TIME_OF_DAY)
    asset_folder = "backgrounds"
    column_list = [
        BackgroundModel.id,
        BackgroundModel.universe_id,
        BackgroundModel.slug,
        BackgroundModel.asset_key,
    ]
    form_columns = [
        BackgroundModel.universe,
        BackgroundModel.slug,
        BackgroundModel.description,
        BackgroundModel.tags,
    ]
    name_plural = "Фоны"
    icon = "fa-solid fa-panorama"


class TagAdmin(ModelView, model=TagModel):
    column_list = [TagModel.id, TagModel.type, TagModel.slug, TagModel.name]
    column_searchable_list = [TagModel.slug, TagModel.name]
    column_filters = [AllUniqueStringValuesFilter(TagModel.type)]
    form_columns = [TagModel.type, TagModel.slug, TagModel.name]
    name_plural = "Теги"
    icon = "fa-solid fa-tags"


ADMIN_VIEWS = [
    UniverseAdmin,
    CharacterAdmin,
    SpriteAdmin,
    OutfitAdmin,
    EmotionAdmin,
    BackgroundAdmin,
    TagAdmin,
]
