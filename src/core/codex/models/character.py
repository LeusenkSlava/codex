from dataclasses import dataclass, field

from src.core.codex.models.tag import Tag


@dataclass(frozen=True, slots=True)
class Character:
    """Персонаж."""

    id: int
    universe_id: int
    slug: str
    name: str
    description: str
    speech_style: dict | None = None
    tags: list[Tag] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Sprite:
    """Спрайт персонажа (базовый слой: тело/поза)."""

    id: int
    character_id: int
    slug: str
    description: str
    asset_key: str
    tags: list[Tag] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Outfit:
    """Одежда персонажа (слой поверх спрайта)."""

    id: int
    sprite_id: int
    slug: str
    name: str
    asset_key: str
    tags: list[Tag] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Emotion:
    """Эмоция персонажа (слой лица поверх спрайта)."""

    id: int
    sprite_id: int
    slug: str
    name: str
    asset_key: str
    tags: list[Tag] = field(default_factory=list)
