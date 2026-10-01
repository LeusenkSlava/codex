from pydantic import BaseModel, ConfigDict

from src.core.codex.models.enum import TagType


class _Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TagSchema(_Schema):
    id: int
    type: TagType
    slug: str
    name: str


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


class EmotionSchema(_Schema):
    id: int
    sprite_id: int
    slug: str
    name: str
    asset_key: str
    tags: list[TagSchema]


class BackgroundSchema(_Schema):
    id: int
    universe_id: int
    slug: str
    description: str
    asset_key: str
    tags: list[TagSchema]
