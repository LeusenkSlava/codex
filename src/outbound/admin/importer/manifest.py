from pydantic import BaseModel, ConfigDict, Field

from src.core.codex.models.enum import Gender


class _Entry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EmotionEntry(_Entry):
    """Эмоция (слой лица) поверх спрайта."""

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    image: str = Field(min_length=1, description="Путь к файлу внутри архива")
    tags: list[str] = Field(default_factory=list)


class OutfitEntry(_Entry):
    """Одежда (слой) поверх спрайта."""

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    image: str = Field(min_length=1, description="Путь к файлу внутри архива")
    tags: list[str] = Field(default_factory=list)


class SpriteEntry(_Entry):
    """Спрайт (базовый слой персонажа)."""

    slug: str = Field(min_length=1)
    description: str = ""
    image: str = Field(min_length=1, description="Путь к файлу внутри архива")
    tags: list[str] = Field(default_factory=list)
    outfits: list[OutfitEntry] = Field(default_factory=list)
    emotions: list[EmotionEntry] = Field(default_factory=list)


class CharacterEntry(_Entry):
    """Персонаж со всеми его слоями."""

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    gender: Gender
    speech_style: dict | None = None
    tags: list[str] = Field(default_factory=list)
    sprites: list[SpriteEntry] = Field(default_factory=list)


class Manifest(_Entry):
    """Корень манифеста."""

    version: int = 1
    universe_slug: str = Field(min_length=1)
    characters: list[CharacterEntry] = Field(min_length=1)
