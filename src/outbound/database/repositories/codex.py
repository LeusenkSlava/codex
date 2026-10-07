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
from src.outbound.database.models.tag import emotion_tags, outfit_tags


class UniverseRepository:
    """Репозиторий вселенных на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def all(self) -> list[Universe]:
        result = await self._session.scalars(
            select(UniverseModel).order_by(UniverseModel.id)
        )
        return [self._to_domain(model) for model in result.all()]

    async def get(self, universe_id: int) -> Universe | None:
        model = await self._session.scalar(
            select(UniverseModel).where(UniverseModel.id == universe_id)
        )
        return self._to_domain(model) if model else None

    @staticmethod
    def _to_domain(model: UniverseModel) -> Universe:
        return Universe(
            id=model.id,
            slug=model.slug,
            title=model.title,
            description=model.description,
        )


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
                tags=[TagRepository._to_tag(t) for t in m.tags],
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
        return [self._to_domain(m) for m in result]

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Sprite]:
        if not character_ids:
            return []

        result = await self._session.scalars(
            select(SpriteModel)
            .where(SpriteModel.character_id.in_(character_ids))
            .options(selectinload(SpriteModel.tags))
            .order_by(SpriteModel.character_id, SpriteModel.id)
        )
        return [self._to_domain(m) for m in result]

    @staticmethod
    def _to_domain(model: SpriteModel) -> Sprite:
        return Sprite(
            id=model.id,
            character_id=model.character_id,
            slug=model.slug,
            description=model.description,
            asset_key=model.asset_key,
            tags=[TagRepository._to_tag(t) for t in model.tags],
        )


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
        return [self._to_domain(m) for m in result]

    async def get_by_sprite_and_tag(
        self, sprite_id: int, tag_slug: str
    ) -> Outfit | None:
        stmt = (
            select(OutfitModel)
            .join(outfit_tags, OutfitModel.id == outfit_tags.c.outfits_id)
            .join(TagModel, TagModel.id == outfit_tags.c.tag_id)
            .where(
                OutfitModel.sprite_id == sprite_id,
                TagModel.slug == tag_slug,
                TagModel.type == TagType.OUTFIT_STYLE,
            )
            .options(selectinload(OutfitModel.tags))
            .order_by(OutfitModel.id.desc())
            .limit(1)
        )
        model = await self._session.scalar(stmt)
        return self._to_domain(model) if model else None

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Возвращает уникальные outfit-теги всей одежды персонажа.

        :param character_id: id персонажа.
        :return: список тегов типа outfit_style без повторений, по алфавиту slug.
        """
        stmt = (
            select(TagModel)
            .join(outfit_tags, TagModel.id == outfit_tags.c.tag_id)
            .join(OutfitModel, OutfitModel.id == outfit_tags.c.outfits_id)
            .join(SpriteModel, SpriteModel.id == OutfitModel.sprite_id)
            .where(
                SpriteModel.character_id == character_id,
                TagModel.type == TagType.OUTFIT_STYLE,
            )
            .distinct()
            .order_by(TagModel.slug)
        )
        result = await self._session.scalars(stmt)
        return [TagRepository._to_tag(m) for m in result]

    @staticmethod
    def _to_domain(model: OutfitModel) -> Outfit:
        return Outfit(
            id=model.id,
            sprite_id=model.sprite_id,
            slug=model.slug,
            name=model.name,
            asset_key=model.asset_key,
            tags=[TagRepository._to_tag(t) for t in model.tags],
        )


class EmotionRepository:
    """Репозиторий эмоций на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        stmt = (
            select(EmotionModel)
            .join(SpriteModel, EmotionModel.sprite_id == SpriteModel.id)
            .where(SpriteModel.character_id == character_id)
            .options(selectinload(EmotionModel.tags), selectinload(EmotionModel.sprite))
            .order_by(EmotionModel.id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Emotion]:
        stmt = (
            select(EmotionModel)
            .join(SpriteModel, EmotionModel.sprite_id == SpriteModel.id)
            .where(SpriteModel.character_id.in_(character_ids))
            .options(selectinload(EmotionModel.tags), selectinload(EmotionModel.sprite))
            .order_by(EmotionModel.id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_by_sprite(self, sprite_id: int) -> list[Emotion]:
        stmt = (
            select(EmotionModel)
            .where(EmotionModel.sprite_id == sprite_id)
            .options(selectinload(EmotionModel.tags), selectinload(EmotionModel.sprite))
            .order_by(EmotionModel.id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Возвращает уникальные emotion-теги всех эмоций персонажа.

        :param character_id: id персонажа.
        :return: список тегов типа emotion (с kind), по алфавиту slug.
        """
        stmt = (
            select(TagModel)
            .join(emotion_tags, TagModel.id == emotion_tags.c.tag_id)
            .join(EmotionModel, EmotionModel.id == emotion_tags.c.emotions_id)
            .join(SpriteModel, SpriteModel.id == EmotionModel.sprite_id)
            .where(
                SpriteModel.character_id == character_id,
                TagModel.type == TagType.EMOTION,
            )
            .distinct()
            .order_by(TagModel.slug)
        )
        result = await self._session.scalars(stmt)
        return [TagRepository._to_tag(m) for m in result]

    @staticmethod
    def _to_domain(model: EmotionModel) -> Emotion:
        return Emotion(
            id=model.id,
            sprite_id=model.sprite_id,
            character_id=model.sprite.character_id,
            slug=model.slug,
            name=model.name,
            asset_key=model.asset_key,
            tags=[TagRepository._to_tag(t) for t in model.tags],
        )


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
                tags=[TagRepository._to_tag(t) for t in m.tags],
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
        return [self._to_tag(m) for m in result]

    async def get_by_slugs(self, slugs: list[str]) -> dict[str, Tag]:
        if not slugs:
            return {}

        stmt = select(TagModel).where(
            TagModel.type == TagType.EMOTION,
            TagModel.slug.in_(slugs),
        )
        result = await self._session.scalars(stmt)
        return {m.slug: self._to_tag(m) for m in result}

    @staticmethod
    def _to_tag(model: TagModel) -> Tag:
        return Tag(
            id=model.id,
            type=model.type,
            slug=model.slug,
            name=model.name,
            kind=model.kind,
        )
