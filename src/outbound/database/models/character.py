from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.outbound.database.models.base_model import BaseModel
from src.outbound.database.models.universe import UniverseModel
from src.outbound.database.models.tag import (
    TagModel,
    character_tags,
    emotion_tags,
    outfit_tags,
    sprite_tags,
)


class SpriteModel(BaseModel):
    """Спрайт (базовый слой персонажа: тело/поза)"""

    __tablename__ = "sprites"
    __table_args__ = (UniqueConstraint("character_id", "slug"),)

    character_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    asset_key: Mapped[str] = mapped_column(String(512), nullable=False)
    # joined: персонаж нужен в __str__ (подпись спрайта в выпадающих списках админки)
    character: Mapped["CharacterModel"] = relationship(lazy="joined")
    tags: Mapped[list[TagModel]] = relationship(secondary=sprite_tags)

    def __str__(self) -> str:
        return f"{self.character.name} / {self.slug}"


class OutfitModel(BaseModel):
    """Одежда (слой поверх спрайта)"""

    __tablename__ = "outfits"
    __table_args__ = (UniqueConstraint("sprite_id", "slug"),)

    sprite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sprite: Mapped[SpriteModel] = relationship()
    tags: Mapped[list[TagModel]] = relationship(secondary=outfit_tags)

    def __str__(self) -> str:
        return self.name


class EmotionModel(BaseModel):
    """Эмоция (слой лица поверх спрайта)"""

    __tablename__ = "emotions"
    __table_args__ = (UniqueConstraint("sprite_id", "slug"),)

    sprite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sprite: Mapped[SpriteModel] = relationship()
    tags: Mapped[list[TagModel]] = relationship(secondary=emotion_tags)

    def __str__(self) -> str:
        return self.name


class CharacterModel(BaseModel):
    """Персонаж"""

    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("universe_id", "slug"),)

    universe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universes.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    speech_style: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    universe: Mapped["UniverseModel"] = relationship()
    tags: Mapped[list[TagModel]] = relationship(secondary=character_tags)

    def __str__(self) -> str:
        return self.name
