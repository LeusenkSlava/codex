from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.codex.models.character import Character, Emotion, Outfit, Sprite
from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background, Universe
from src.outbound.database.models import (
    BackgroundModel,
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
    TagModel,
    UniverseModel,
)


def _to_tag(model: TagModel) -> Tag:
    return Tag(id=model.id, type=model.type, slug=model.slug, name=model.name)


def _to_emotion(model: EmotionModel) -> Emotion:
    return Emotion(
        id=model.id,
        sprite_id=model.sprite_id,
        slug=model.slug,
        name=model.name,
        asset_key=model.asset_key,
        tags=[_to_tag(t) for t in model.tags],
    )


class UniverseRepository:
    """Репозиторий вселенных на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Universe]:
        result = await self._session.scalars(select(UniverseModel).order_by(UniverseModel.id))
        return [
            Universe(id=m.id, slug=m.slug, title=m.title, description=m.description)
            for m in result
        ]


class CharacterRepository:
    """Репозиторий персонажей на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_universe(self, universe_id: int) -> list[Character]:
        stmt = (
            select(CharacterModel)
            .where(CharacterModel.universe_id == universe_id)
            .options(selectinload(CharacterModel.tags))
            .order_by(CharacterModel.id)
        )
        result = await self._session.scalars(stmt)
        return [
            Character(
                id=m.id,
                universe_id=m.universe_id,
                slug=m.slug,
                name=m.name,
                description=m.description,
                speech_style=m.speech_style,
                tags=[_to_tag(t) for t in m.tags],
            )
            for m in result
        ]


class SpriteRepository:
    """Репозиторий спрайтов на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_character(self, character_id: int) -> list[Sprite]:
        stmt = (
            select(SpriteModel)
            .where(SpriteModel.character_id == character_id)
            .options(selectinload(SpriteModel.tags))
            .order_by(SpriteModel.id)
        )
        result = await self._session.scalars(stmt)
        return [
            Sprite(
                id=m.id,
                character_id=m.character_id,
                slug=m.slug,
                description=m.description,
                asset_key=m.asset_key,
                tags=[_to_tag(t) for t in m.tags],
            )
            for m in result
        ]


class OutfitRepository:
    """Репозиторий одежды на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        stmt = (
            select(OutfitModel)
            .where(OutfitModel.sprite_id == sprite_id)
            .options(selectinload(OutfitModel.tags))
            .order_by(OutfitModel.id)
        )
        result = await self._session.scalars(stmt)
        return [
            Outfit(
                id=m.id,
                sprite_id=m.sprite_id,
                slug=m.slug,
                name=m.name,
                asset_key=m.asset_key,
                tags=[_to_tag(t) for t in m.tags],
            )
            for m in result
        ]


class EmotionRepository:
    """Репозиторий эмоций на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        stmt = (
            select(EmotionModel)
            .join(SpriteModel, EmotionModel.sprite_id == SpriteModel.id)
            .where(SpriteModel.character_id == character_id)
            .options(selectinload(EmotionModel.tags))
            .order_by(EmotionModel.id)
        )
        result = await self._session.scalars(stmt)
        return [_to_emotion(m) for m in result]

    async def get_by_sprite(self, sprite_id: int) -> list[Emotion]:
        stmt = (
            select(EmotionModel)
            .where(EmotionModel.sprite_id == sprite_id)
            .options(selectinload(EmotionModel.tags))
            .order_by(EmotionModel.id)
        )
        result = await self._session.scalars(stmt)
        return [_to_emotion(m) for m in result]


class BackgroundRepository:
    """Репозиторий задников на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        stmt = (
            select(BackgroundModel)
            .where(BackgroundModel.universe_id == universe_id)
            .options(selectinload(BackgroundModel.tags))
            .order_by(BackgroundModel.id)
        )
        result = await self._session.scalars(stmt)
        return [
            Background(
                id=m.id,
                universe_id=m.universe_id,
                slug=m.slug,
                description=m.description,
                asset_key=m.asset_key,
                tags=[_to_tag(t) for t in m.tags],
            )
            for m in result
        ]


class TagRepository:
    """Репозиторий тегов на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_type(self, tag_type: TagType) -> list[Tag]:
        stmt = select(TagModel).where(TagModel.type == tag_type).order_by(TagModel.slug)
        result = await self._session.scalars(stmt)
        return [_to_tag(m) for m in result]
