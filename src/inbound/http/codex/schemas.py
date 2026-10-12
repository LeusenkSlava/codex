from pydantic import BaseModel, ConfigDict, Field

from src.core.codex.models.enum import TagKind, TagType


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


class CharacterSchema(_Schema):
    id: int
    universe_id: int
    slug: str
    name: str
    description: str
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
    """Тело запроса подбора одной одежды по тегу."""

    tag: str = Field(
        description=(
            "Slug одного тега одежды (outfit_style). Если подходит несколько "
            "вариантов, вернётся одежда с наибольшим id."
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


class EmotionTagsResponse(_Schema):
    """Доступные персонажу emotion-теги, разделённые по роли."""

    base: list[TagSchema] = Field(
        description="Базовые эмоции (kind=base), доступные персонажу.",
    )
    modifiers: list[TagSchema] = Field(
        description="Модификаторы (kind=modifier), доступные персонажу.",
    )


class EmotionTagsRequest(_Schema):
    """Тело запроса подбора одной эмоции.

    Модель выбирает только смысл и не знает slug'и спрайтов, поэтому отправляет
    набор тегов-смыслов. Ровно один тег должен иметь `kind=base`
    (обязательная эмоция), остальные — необязательные уточнения `modifier`.
    Порядок тегов не важен. Если передан `sprite_id`, эмоции этого спрайта
    считаются более подходящими.
    """

    sprite_id: int | None = Field(
        default=None,
        description=(
            "id спрайта (необязательно). Если задан, эмоции этого спрайта получают "
            "приоритет перед эмоциями других спрайтов персонажа."
        ),
        examples=[1],
    )
    tags: list[str] = Field(
        description=(
            "Slug'и тегов-смыслов. Ровно один `base` (например `happy`, `sad`, "
            "`angry`) + 0..N `modifier` (например `blush`, `crying`, `looking_away`). "
            "Порядок не важен."
        ),
        examples=[["happy", "blush"], ["sad", "crying", "looking_away"]],
    )


class EmotionMatchItem(_Schema):
    """Элемент батча подбора эмоций: персонаж + набор тегов-смыслов."""

    character_id: int = Field(
        description="id персонажа, для которого подбирается эмоция.",
        examples=[1],
    )
    sprite_id: int | None = Field(
        default=None,
        description=(
            "id спрайта (необязательно). Если задан, эмоции этого спрайта получают "
            "приоритет перед эмоциями других спрайтов персонажа."
        ),
        examples=[1],
    )
    tags: list[str] = Field(
        description=(
            "Slug'и тегов-смыслов. Ровно один `base` + 0..N `modifier`. "
            "Порядок не важен."
        ),
        examples=[["happy", "blush"]],
    )


class BackgroundSchema(_Schema):
    id: int
    universe_id: int
    slug: str
    description: str
    asset_key: str
    tags: list[TagSchema]


class BackgroundTagsResponse(_Schema):
    """Доступные вселенной теги задников, разделённые по роли (kind).

    `base` — локации (ровно один на задник), `modifiers` — уточнения: время
    суток, внутри/снаружи, свет, люди и т.п.
    """

    base: list[TagSchema] = Field(
        description="Локации (kind=base), встречающиеся у задников вселенной.",
    )
    modifiers: list[TagSchema] = Field(
        description=(
            "Модификаторы (kind=modifier): время суток, внутри/снаружи, свет, люди."
        ),
    )


class BackgroundTagsRequest(_Schema):
    """Тело запроса подбора задника.

    Модель выбирает только смысл и не знает slug'и задников, поэтому отправляет
    набор тегов-смыслов. Ровно один тег должен иметь `kind=base` (локация),
    остальные — необязательные уточнения `kind=modifier`.
    Порядок тегов не важен.
    """

    tags: list[str] = Field(
        description=(
            "Slug'и тегов-смыслов. Ровно один `base` (например `library`, "
            "`square`, `dining_room`) + 0..N `modifier` (например `night`, "
            "`inside`, `light_turn_off`). Порядок не важен."
        ),
        examples=[["library", "night"], ["library", "inside", "day"]],
    )


class BackgroundMatchItem(_Schema):
    """Элемент батча подбора задников: вселенная + набор тегов-смыслов."""

    universe_id: int = Field(
        description="id вселенной, для которой подбирается задник.",
        examples=[1],
    )
    tags: list[str] = Field(
        description=(
            "Slug'и тегов-смыслов. Ровно один `base` + 0..N `modifier`. "
            "Порядок не важен."
        ),
        examples=[["library", "night"]],
    )

