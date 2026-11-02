from sqladmin import ModelView

from src.core.codex.models.enum import TagType
from src.outbound.admin.views.filters import ForeignKeyObjectFilter, TagFilter
from src.outbound.admin.views.mixins import (
    AssetUploadMixin,
    MediaCleanupMixin,
    TagTypeFilterMixin,
    UniverseScopedMixin,
    _tags_formatter,
)
from src.outbound.database.models.character import (
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
)
from src.outbound.database.models.universe import UniverseModel


class CharacterAdmin(UniverseScopedMixin, MediaCleanupMixin, ModelView, model=CharacterModel):
    # В форме создания поле «Вселенная» подставляется из активной вселенной.
    universe_default_field = "universe"
    column_list = [
        CharacterModel.id,
        CharacterModel.universe,
        CharacterModel.slug,
        CharacterModel.name,
        CharacterModel.gender,
        CharacterModel.tags,
    ]
    column_searchable_list = [CharacterModel.slug, CharacterModel.name]
    column_filters = [
        ForeignKeyObjectFilter(
            CharacterModel.universe_id, UniverseModel, title="Вселенная"
        ),
        TagFilter((TagType.ARCHETYPE,), title="Архетип"),
    ]
    column_formatters = {"tags": _tags_formatter}
    column_formatters_detail = {"tags": _tags_formatter}
    # tags — M2M: sqladmin отрисует мультиселект по уже созданным тегам.
    form_columns = [
        CharacterModel.universe,
        CharacterModel.slug,
        CharacterModel.name,
        CharacterModel.gender,
        CharacterModel.description,
        CharacterModel.speech_style,
        CharacterModel.tags,
    ]
    name_plural = "Персонажи"
    icon = "fa-solid fa-user"


class SpriteAdmin(UniverseScopedMixin, MediaCleanupMixin, AssetUploadMixin, ModelView, model=SpriteModel):
    # Селектор персонажа: все персонажи выбранной вселенной, поиск необязателен.
    scoped_relation_fields = ("character",)
    asset_folder = "sprites"
    column_list = [
        SpriteModel.id,
        SpriteModel.character,
        SpriteModel.slug,
        SpriteModel.tags,
        SpriteModel.asset_key,
    ]
    column_filters = [
        ForeignKeyObjectFilter(
            SpriteModel.character_id, CharacterModel, title="Персонаж"
        ),
        TagFilter(tuple(TagType), title="Тег"),
    ]
    form_columns = [
        SpriteModel.character,
        SpriteModel.slug,
        SpriteModel.description,
        SpriteModel.tags,
    ]
    name_plural = "Спрайты"
    icon = "fa-solid fa-image"


class OutfitAdmin(UniverseScopedMixin, TagTypeFilterMixin, AssetUploadMixin, ModelView, model=OutfitModel):
    # Селектор спрайта: все спрайты выбранной вселенной, поиск необязателен.
    scoped_relation_fields = ("sprite",)
    tag_types = (TagType.OUTFIT_STYLE,)
    asset_folder = "outfits"
    column_list = [
        OutfitModel.id,
        OutfitModel.sprite,
        OutfitModel.slug,
        OutfitModel.name,
        OutfitModel.tags,
        OutfitModel.asset_key,
    ]
    column_searchable_list = [OutfitModel.slug, OutfitModel.name]
    column_filters = [
        ForeignKeyObjectFilter(OutfitModel.sprite_id, SpriteModel, title="Спрайт"),
        TagFilter((TagType.OUTFIT_STYLE,), title="Стиль"),
    ]
    form_columns = [
        OutfitModel.sprite,
        OutfitModel.slug,
        OutfitModel.name,
        OutfitModel.tags,
    ]
    name_plural = "Одежда"
    icon = "fa-solid fa-shirt"


class EmotionAdmin(UniverseScopedMixin, TagTypeFilterMixin, AssetUploadMixin, ModelView, model=EmotionModel):
    # Селектор спрайта: все спрайты выбранной вселенной, поиск необязателен.
    scoped_relation_fields = ("sprite",)
    tag_types = (TagType.EMOTION,)
    asset_folder = "emotions"
    column_list = [
        EmotionModel.id,
        EmotionModel.sprite,
        EmotionModel.slug,
        EmotionModel.name,
        EmotionModel.tags,
        EmotionModel.asset_key,
    ]
    column_searchable_list = [EmotionModel.slug, EmotionModel.name]
    column_filters = [
        ForeignKeyObjectFilter(EmotionModel.sprite_id, SpriteModel, title="Спрайт"),
        TagFilter((TagType.EMOTION,), title="Эмоция"),
    ]
    form_columns = [
        EmotionModel.sprite,
        EmotionModel.slug,
        EmotionModel.name,
        EmotionModel.tags,
    ]
    name_plural = "Эмоции"
    icon = "fa-solid fa-face-smile"
