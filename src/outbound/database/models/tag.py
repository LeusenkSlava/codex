from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.codex.models.enum import TagType
from src.outbound.database.models.base_model import Base, BaseModel
from src.outbound.database.utils import pg_enum


class TagModel(BaseModel):
    """Пространство тегов"""

    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("type", "slug"),
        Index("ix_tags_type", "type"),
    )

    type: Mapped[TagType] = mapped_column(pg_enum(TagType), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    def __str__(self) -> str:
        return f"{self.type}: {self.name}"


def _tag_link_table(name: str, owner_table: str) -> Table:
    """Фабрика M2M-таблиц owner<->tag, чтобы не дублировать определение."""
    return Table(
        name,
        Base.metadata,
        Column(
            f"{owner_table}_id",
            Integer,
            ForeignKey(f"{owner_table}.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column(
            "tag_id",
            Integer,
            ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


sprite_tags = _tag_link_table("sprite_tags", "sprites")
outfit_tags = _tag_link_table("outfit_tags", "outfits")
emotion_tags = _tag_link_table("emotion_tags", "emotions")
background_tags = _tag_link_table("background_tags", "backgrounds")
character_tags = _tag_link_table("character_tags", "characters")
