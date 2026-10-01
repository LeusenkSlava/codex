from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.outbound.database.models.base_model import BaseModel
from src.outbound.database.models.tag import TagModel, background_tags


class BackgroundModel(BaseModel):
    """Локация"""

    __tablename__ = "backgrounds"
    __table_args__ = (UniqueConstraint("universe_id", "slug"),)

    universe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universes.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    asset_key: Mapped[str] = mapped_column(String(512), nullable=False)

    universe: Mapped["UniverseModel"] = relationship()
    tags: Mapped[list[TagModel]] = relationship(secondary=background_tags)

    def __str__(self) -> str:
        return self.slug


class UniverseModel(BaseModel):
    __tablename__ = "universes"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    def __str__(self) -> str:
        return self.title
