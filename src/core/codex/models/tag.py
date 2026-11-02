from dataclasses import dataclass

from src.core.codex.models.enum import TagKind, TagType


@dataclass(frozen=True, slots=True)
class Tag:
    """Тег: `type` задаёт сущность, `kind` — роль в подборе (`base`/`modifier`)."""

    id: int
    type: TagType
    slug: str
    name: str
    kind: TagKind | None = None
