from sqladmin import ModelView

from src.core.codex.models.enum import TagType
from src.outbound.admin.views.filters import ForeignKeyObjectFilter, TagFilter
from src.outbound.admin.views.mixins import (
    AssetUploadMixin,
    MediaCleanupMixin,
    TagTypeFilterMixin,
    _tags_formatter,
)
from src.outbound.database.models.character import (
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
)
from src.outbound.database.models.universe import UniverseModel


class CharacterAdmin(MediaCleanupMixin, ModelView, model=CharacterModel):
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
    # tags - M2M, sqladmin отрисует как multi-select по уже созданным TagModel
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


class SpriteAdmin(MediaCleanupMixin, AssetUploadMixin, ModelView, model=SpriteModel):
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


class OutfitAdmin(TagTypeFilterMixin, AssetUploadMixin, ModelView, model=OutfitModel):
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


class EmotionAdmin(TagTypeFilterMixin, AssetUploadMixin, ModelView, model=EmotionModel):
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
