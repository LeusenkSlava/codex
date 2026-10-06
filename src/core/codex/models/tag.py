from dataclasses import dataclass

from src.core.codex.models.enum import TagKind, TagType


@dataclass(frozen=True, slots=True)
class Tag:
    """Тег."""

    id: int
    type: TagType
    slug: str
    name: str
    kind: TagKind | None = None
