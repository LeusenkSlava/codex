from sqladmin import ModelView

from src.core.codex.models.enum import TagType
from src.outbound.admin.views.filters import ForeignKeyObjectFilter, TagFilter
from src.outbound.admin.views.mixins import (
    AssetUploadMixin,
    MediaCleanupMixin,
    TagTypeFilterMixin,
)
from src.outbound.database.models.universe import BackgroundModel, UniverseModel


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


class BackgroundAdmin(
    TagTypeFilterMixin, AssetUploadMixin, ModelView, model=BackgroundModel
):
    tag_types = (TagType.LOCATION, TagType.TIME_OF_DAY)
    asset_folder = "backgrounds"
    column_list = [
        BackgroundModel.id,
        BackgroundModel.universe,
        BackgroundModel.slug,
        BackgroundModel.tags,
        BackgroundModel.asset_key,
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
        BackgroundModel.slug,
        BackgroundModel.description,
        BackgroundModel.tags,
    ]
    name_plural = "Фоны"
    icon = "fa-solid fa-panorama"
