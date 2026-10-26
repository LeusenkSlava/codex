from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.codex.models.character import Character, Emotion, Outfit, Sprite
from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag
from src.outbound.database.models import (
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
    TagModel,
)
from src.outbound.database.models.tag import emotion_tags, outfit_tags
from src.outbound.database.repositories.tag import TagRepository


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
        return [self._to_domain(m) for m in result]

    @staticmethod
    def _to_domain(model: CharacterModel) -> Character:
        return Character(
            id=model.id,
            universe_id=model.universe_id,
            slug=model.slug,
            name=model.name,
            description=model.description,
            gender=model.gender,
            speech_style=model.speech_style,
            tags=[TagRepository._to_domain(t) for t in model.tags],
        )


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

    async def get_by_id(self, sprite_id: int) -> Sprite | None:
        stmt = (
            select(SpriteModel)
            .where(SpriteModel.id == sprite_id)
            .options(selectinload(SpriteModel.tags))
        )
        model = await self._session.scalar(stmt)
        return self._to_domain(model) if model else None

    @staticmethod
    def _to_domain(model: SpriteModel) -> Sprite:
        return Sprite(
            id=model.id,
            character_id=model.character_id,
            slug=model.slug,
            description=model.description,
            asset_key=model.asset_key,
            tags=[TagRepository._to_domain(t) for t in model.tags],
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

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Outfit]:
        if not character_ids:
            return []

        stmt = (
            select(OutfitModel)
            .join(SpriteModel, OutfitModel.sprite_id == SpriteModel.id)
            .where(SpriteModel.character_id.in_(character_ids))
            .options(selectinload(OutfitModel.tags))
            .order_by(SpriteModel.character_id, OutfitModel.id)
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

    async def get_by_character_and_tag(
        self, character_id: int, tag_slug: str
    ) -> list[Outfit]:
        stmt = (
            select(OutfitModel)
            .join(SpriteModel, OutfitModel.sprite_id == SpriteModel.id)
            .join(outfit_tags, OutfitModel.id == outfit_tags.c.outfits_id)
            .join(TagModel, TagModel.id == outfit_tags.c.tag_id)
            .where(
                SpriteModel.character_id == character_id,
                TagModel.slug == tag_slug,
                TagModel.type == TagType.OUTFIT_STYLE,
            )
            .options(selectinload(OutfitModel.tags))
            .order_by(OutfitModel.id.desc())
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

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
        return [TagRepository._to_domain(m) for m in result]

    @staticmethod
    def _to_domain(model: OutfitModel) -> Outfit:
        return Outfit(
            id=model.id,
            sprite_id=model.sprite_id,
            slug=model.slug,
            name=model.name,
            asset_key=model.asset_key,
            tags=[TagRepository._to_domain(t) for t in model.tags],
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
        return [TagRepository._to_domain(m) for m in result]

    @staticmethod
    def _to_domain(model: EmotionModel) -> Emotion:
        return Emotion(
            id=model.id,
            sprite_id=model.sprite_id,
            character_id=model.sprite.character_id,
            slug=model.slug,
            name=model.name,
            asset_key=model.asset_key,
            tags=[TagRepository._to_domain(t) for t in model.tags],
        )
