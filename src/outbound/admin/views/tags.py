from sqladmin import ModelView
from sqladmin.filters import AllUniqueStringValuesFilter

from src.outbound.database.models.tag import TagModel


class TagAdmin(ModelView, model=TagModel):
    column_list = [
        TagModel.id,
        TagModel.type,
        TagModel.kind,
        TagModel.slug,
        TagModel.name,
    ]
    column_searchable_list = [TagModel.slug, TagModel.name]
    column_filters = [
        AllUniqueStringValuesFilter(TagModel.type),
        AllUniqueStringValuesFilter(TagModel.kind),
    ]
    form_columns = [TagModel.type, TagModel.kind, TagModel.slug, TagModel.name]
    name_plural = "Теги"
    icon = "fa-solid fa-tags"
