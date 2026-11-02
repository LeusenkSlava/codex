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
        description="URL обложки или `null`, если её нет.",
        examples=["/media/universes/6d6bd9c091b44c719149152ef007d6eb.png"],
    )


class UniverseListResponse(_Schema):
    items: list[UniverseSchema] = Field(description="Вселенные текущей страницы.")
    total: int = Field(description="Всего вселенных по фильтру.")
    offset: int = Field(description="Значение параметра `offset` запроса.")
    limit: int = Field(description="Значение параметра `limit` запроса.")


class CharacterSchema(_Schema):
    id: int
    universe_id: int
    slug: str
    name: str
    description: str
    gender: Gender = Field(examples=["female"])
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
    tag: str = Field(
        description=(
            "Slug тега `outfit_style`. При нескольких совпадениях берётся одежда "
            "с большим `id`."
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
    slug: str = Field(description="Slug тега `emotion`.", examples=["rage"])
    name: str = Field(description="Название тега.", examples=["Кричит"])
    kind: TagKind | None = Field(
        default=None,
        description="`base` или `modifier`.",
        examples=["base"],
    )


class OutfitWithEmotionsSchema(_Schema):
    outfit_tag: str = Field(
        description="Slug тега `outfit_style` с `kind=base`.",
        examples=["camp_uniform"],
    )
    name: str = Field(
        description="Название тега.",
        examples=["Форма вожатого"],
    )
    emotions: list[OutfitEmotionSchema] = Field(
        description=(
            "Теги эмоций, доступных для одежды с этим тегом: сначала `base`, "
            "затем `modifier`."
        ),
    )


class EmotionTagsResponse(_Schema):
    base: list[TagSchema] = Field(description="Теги с `kind=base`.")
    modifiers: list[TagSchema] = Field(description="Теги с `kind=modifier`.")


class EmotionTagsRequest(_Schema):
    sprite_id: int | None = Field(
        default=None,
        description="Если указан, эмоции этого спрайта получают приоритет.",
        examples=[1],
    )
    tags: list[str] = Field(
        description="Slug'и тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["happy", "blush"], ["sad", "crying", "looking_away"]],
    )


class EmotionMatchItem(_Schema):
    character_id: int = Field(
        description="id персонажа.",
        examples=[1],
    )
    sprite_id: int | None = Field(
        default=None,
        description="Если указан, эмоции этого спрайта получают приоритет.",
        examples=[1],
    )
    tags: list[str] = Field(
        description="Slug'и тегов: ровно один `base` + 0..N `modifier`.",
        examples=[["happy", "blush"]],
    )


class VisualsMatchRequest(_Schema):
    outfit_tag: str = Field(
        description="Slug тега `outfit_style`.",
        examples=["red-dress"],
    )
    emotion_tags: list[str] = Field(
        description="Slug'и тегов `emotion`: ровно один `base` + 0..N `modifier`.",
        examples=[["angry", "soft"]],
    )


class VisualsMatchResponse(_Schema):
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
    base: list[TagSchema] = Field(description="Теги с `kind=base` (локации).")
    modifiers: list[TagSchema] = Field(description="Теги с `kind=modifier`.")


class BackgroundTagsRequest(_Schema):
    tags: list[str] = Field(
        description=(
            "Slug'и тегов `location` и `time_of_day`: ровно один `base` + 0..N "
            "`modifier`."
        ),
        examples=[["library", "night"], ["library", "inside", "day"]],
    )


class BackgroundMatchItem(_Schema):
    universe_id: int = Field(
        description="id вселенной.",
        examples=[1],
    )
    tags: list[str] = Field(
        description=(
            "Slug'и тегов `location` и `time_of_day`: ровно один `base` + 0..N "
            "`modifier`."
        ),
        examples=[["library", "night"]],
    )
