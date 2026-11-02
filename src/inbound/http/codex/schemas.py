from pydantic import BaseModel, ConfigDict, Field

from src.core.codex.models.enum import Gender, TagKind, TagType


class _Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TagSchema(_Schema):
    id: int
    type: TagType
    slug: str
    name: str
    kind: TagKind | None = None


class UniverseSchema(_Schema):
    id: int
    slug: str
    title: str
    description: str
    cover_asset_key: str | None = Field(
        default=None,
        description="URL обложки или `null`, если она не загружена.",
        examples=["/media/universes/6d6bd9c091b44c719149152ef007d6eb.png"],
    )


class UniverseListResponse(_Schema):
    """Страница вселенных."""

    items: list[UniverseSchema] = Field(description="Вселенные на странице.")
    total: int = Field(description="Всего вселенных по фильтру.")
    offset: int = Field(description="Сколько пропущено.")
    limit: int = Field(description="Размер страницы.")


class CharacterSchema(_Schema):
    id: int
    universe_id: int
    slug: str
    name: str
    description: str
    gender: Gender = Field(description="`male` или `female`.", examples=["female"])
    speech_style: dict | None
    tags: list[TagSchema]


class SpriteSchema(_Schema):
    id: int
    character_id: int
    slug: str
    description: str
    asset_key: str
    tags: list[TagSchema]


class OutfitSchema(_Schema):
    id: int
    sprite_id: int
    slug: str
    name: str
    asset_key: str
    tags: list[TagSchema]


class OutfitMatchRequest(_Schema):
    """Тело запроса подбора одежды."""

    tag: str = Field(
        description=(
            "Slug тега одежды (`outfit_style`). При нескольких совпадениях "
            "вернётся одежда с большим `id`."
        ),
        examples=["casual"],
    )


class EmotionSchema(_Schema):
    id: int
    sprite_id: int
    slug: str
    name: str
    asset_key: str
    tags: list[TagSchema]


class OutfitEmotionSchema(_Schema):
    """Эмоция, доступная для одежды."""

    slug: str = Field(description="Slug emotion-тега.", examples=["rage"])
    name: str = Field(description="Название emotion-тега.", examples=["Кричит"])
    kind: TagKind | None = Field(
        default=None,
        description="`base` или `modifier`.",
        examples=["base"],
    )


class OutfitWithEmotionsSchema(_Schema):
    """Тег стиля одежды и доступные для него эмоции."""

    outfit_tag: str = Field(
        description="Slug тега стиля одежды (`outfit_style`, `kind=base`).",
        examples=["camp_uniform"],
    )
    name: str = Field(
        description="Название тега стиля одежды.",
        examples=["Форма вожатого"],
    )
    emotions: list[OutfitEmotionSchema] = Field(
        description="Emotion-теги одежды: сначала `base`, затем `modifier`.",
    )


class EmotionTagsResponse(_Schema):
    """Emotion-теги персонажа по роли."""

    base: list[TagSchema] = Field(
        description="Базовые эмоции (`kind=base`).",
    )
    modifiers: list[TagSchema] = Field(
        description="Уточнения (`kind=modifier`).",
    )


class EmotionTagsRequest(_Schema):
    """Тело запроса подбора эмоции.

    Ровно один тег должен быть `base`, остальные — `modifier`.
    """

    sprite_id: int | None = Field(
        default=None,
        description="id спрайта: его эмоции получают приоритет.",
        examples=[1],
    )
    tags: list[str] = Field(
        description="Slug'и тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["happy", "blush"], ["sad", "crying", "looking_away"]],
    )


class EmotionMatchItem(_Schema):
    """Элемент батча подбора эмоций."""

    character_id: int = Field(
        description="id персонажа.",
        examples=[1],
    )
    sprite_id: int | None = Field(
        default=None,
        description="id спрайта: его эмоции получают приоритет.",
        examples=[1],
    )
    tags: list[str] = Field(
        description="Slug'и тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["happy", "blush"]],
    )


class VisualsMatchRequest(_Schema):
    """Тело запроса подбора спрайта, наряда и эмоции."""

    outfit_tag: str = Field(
        description="Slug тега одежды (`outfit_style`).",
        examples=["red-dress"],
    )
    emotion_tags: list[str] = Field(
        description="Slug'и emotion-тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["angry", "soft"]],
    )


class VisualsMatchResponse(_Schema):
    """Подобранные визуальные слои."""

    sprite_asset_key: str = Field(description="asset_key спрайта.")
    outfit_asset_key: str = Field(description="asset_key наряда.")
    emotion_asset_key: str | None = Field(
        description="asset_key эмоции или `null`, если эмоция не найдена.",
    )


class BackgroundSchema(_Schema):
    id: int
    universe_id: int
    slug: str
    description: str
    asset_key: str
    sound_asset_key: str | None = None
    tags: list[TagSchema]


class BackgroundTagsResponse(_Schema):
    """Теги задников вселенной по роли."""

    base: list[TagSchema] = Field(
        description="Локации (`kind=base`).",
    )
    modifiers: list[TagSchema] = Field(
        description="Уточнения (`kind=modifier`).",
    )


class BackgroundTagsRequest(_Schema):
    """Тело запроса подбора задника.

    Ровно один тег должен быть `base` (локация), остальные — `modifier`.
    """

    tags: list[str] = Field(
        description="Slug'и тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["library", "night"], ["library", "inside", "day"]],
    )


class BackgroundMatchItem(_Schema):
    """Элемент батча подбора задников."""

    universe_id: int = Field(
        description="id вселенной.",
        examples=[1],
    )
    tags: list[str] = Field(
        description="Slug'и тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["library", "night"]],
    )
