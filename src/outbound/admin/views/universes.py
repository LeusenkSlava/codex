from sqladmin import ModelView

from src.core.codex.models.enum import TagType
from src.outbound.admin.views.filters import ForeignKeyObjectFilter, TagFilter
from src.outbound.admin.views.mixins import (
    AssetUploadMixin,
    MediaCleanupMixin,
    TagTypeFilterMixin,
    _audio_preview,
    _image_preview,
    _tags_formatter,
)
from src.outbound.database.models.universe import (
    BackgroundModel,
    SoundModel,
    UniverseModel,
)
from src.outbound.media.storage import IMAGE_EXTENSIONS


class UniverseAdmin(
    AssetUploadMixin, MediaCleanupMixin, ModelView, model=UniverseModel
):
    """Вселенные; обложка необязательна."""

    asset_folder = "universes"
    asset_attribute = "cover_asset_key"
    asset_label = "Обложка"
    asset_extensions = IMAGE_EXTENSIONS
    asset_required = False
    column_list = [
        UniverseModel.id,
        UniverseModel.slug,
        UniverseModel.title,
        UniverseModel.cover_asset_key,
    ]
    column_searchable_list = [UniverseModel.slug, UniverseModel.title]
    column_formatters = {"cover_asset_key": _image_preview}
    column_formatters_detail = {"cover_asset_key": _image_preview}
    column_labels = {"cover_asset_key": "Обложка"}
    form_columns = [
        UniverseModel.slug,
        UniverseModel.title,
        UniverseModel.description,
    ]
    name_plural = "Вселенные"
    icon = "fa-solid fa-globe"


class BackgroundAdmin(
    TagTypeFilterMixin, AssetUploadMixin, ModelView, model=BackgroundModel
):
    tag_types = (TagType.LOCATION, TagType.TIME_OF_DAY)
    asset_folder = "backgrounds"
    column_list = [
        BackgroundModel.universe,
        BackgroundModel.slug,
        BackgroundModel.asset_key,
        BackgroundModel.tags,
    ]
    column_filters = [
        ForeignKeyObjectFilter(
            BackgroundModel.universe_id, UniverseModel, title="Вселенная"
        ),
        TagFilter(
            (TagType.LOCATION,), title="Локация", parameter_name="location_tag_id"
        ),
        TagFilter(
            (TagType.TIME_OF_DAY,),
            title="Время суток",
            parameter_name="time_of_day_tag_id",
        ),
    ]
    form_columns = [
        BackgroundModel.universe,
        BackgroundModel.sound,
        BackgroundModel.slug,
        BackgroundModel.description,
        BackgroundModel.tags,
    ]
    name_plural = "Фоны"
    icon = "fa-solid fa-panorama"


class SoundAdmin(TagTypeFilterMixin, AssetUploadMixin, ModelView, model=SoundModel):
    tag_types = (TagType.MUSIC, TagType.SFX)
    asset_folder = "sounds"
    asset_label = "Аудиофайл"
    column_list = [
        SoundModel.id,
        SoundModel.universe,
        SoundModel.slug,
        SoundModel.tags,
        SoundModel.asset_key,
    ]
    column_searchable_list = [SoundModel.slug]
    column_formatters = {"asset_key": _audio_preview, "tags": _tags_formatter}
    column_formatters_detail = {"asset_key": _audio_preview, "tags": _tags_formatter}
    column_filters = [
        ForeignKeyObjectFilter(
            SoundModel.universe_id, UniverseModel, title="Вселенная"
        ),
        TagFilter((TagType.MUSIC,), title="Музыка", parameter_name="music_tag_id"),
        TagFilter((TagType.SFX,), title="Эффекты", parameter_name="sfx_tag_id"),
    ]
    form_columns = [
        SoundModel.universe,
        SoundModel.slug,
        SoundModel.description,
        SoundModel.tags,
    ]
    name_plural = "Звуки"
    icon = "fa-solid fa-music"
