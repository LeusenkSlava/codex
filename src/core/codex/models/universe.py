from dataclasses import dataclass, field

from src.core.codex.models.tag import Tag


@dataclass(frozen=True, slots=True)
class Universe:
    """Вселенная."""

    id: int
    slug: str
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class Background:
    """Задник (локация)."""

    id: int
    universe_id: int
    slug: str
    description: str
    asset_key: str
    tags: list[Tag] = field(default_factory=list)
