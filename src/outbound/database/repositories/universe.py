from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background, Sound, Universe
from src.outbound.database.models import (
    BackgroundModel,
    SoundModel,
    TagModel,
    UniverseModel,
)
from src.outbound.database.models.tag import background_tags
from src.outbound.database.repositories.tag import TagRepository

# Типы тегов, которыми размечен задник: локация (обязательная) + время суток.
_BACKGROUND_TAG_TYPES = (TagType.LOCATION, TagType.TIME_OF_DAY)


class UniverseRepository:
    """Репозиторий вселенных на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self, query: str | None = None, offset: int = 0, limit: int = 20
    ) -> tuple[list[Universe], int]:
        """Возвращает страницу вселенных и их общее число.

        :param query: необязательная подстрока для поиска по названию (title),
            без учёта регистра.
        :param offset: сколько вселенных пропустить.
        :param limit: максимальное число вселенных в странице.
        :return: кортеж ``(вселенные, всего найдено)``.
        """
        stmt = select(UniverseModel)
        count_stmt = select(func.count()).select_from(UniverseModel)

        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(UniverseModel.title.ilike(pattern))
            count_stmt = count_stmt.where(UniverseModel.title.ilike(pattern))

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.scalars(
            stmt.order_by(UniverseModel.id).offset(offset).limit(limit)
        )
        return [self._to_domain(model) for model in result.all()], total

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
            cover_asset_key=model.cover_asset_key,
        )


class BackgroundRepository:
    """Репозиторий задников на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        stmt = (
            select(BackgroundModel)
            .where(BackgroundModel.universe_id == universe_id)
            .options(selectinload(BackgroundModel.tags), selectinload(BackgroundModel.sound))
            .order_by(BackgroundModel.id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_by_universe_ids(self, universe_ids: list[int]) -> list[Background]:
        if not universe_ids:
            return []

        stmt = (
            select(BackgroundModel)
            .where(BackgroundModel.universe_id.in_(universe_ids))
            .options(selectinload(BackgroundModel.tags), selectinload(BackgroundModel.sound))
            .order_by(BackgroundModel.universe_id, BackgroundModel.id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_by_id(self, background_id: int) -> Background | None:
        stmt = (
            select(BackgroundModel)
            .where(BackgroundModel.id == background_id)
            .options(selectinload(BackgroundModel.tags), selectinload(BackgroundModel.sound))
        )
        model = await self._session.scalar(stmt)
        return self._to_domain(model) if model else None

    async def get_tags_by_universe(self, universe_id: int) -> list[Tag]:
        """Возвращает уникальные теги задников вселенной.

        :param universe_id: id вселенной.
        :return: теги типов location и time_of_day без повторений, по алфавиту slug.
        """
        stmt = (
            select(TagModel)
            .join(background_tags, TagModel.id == background_tags.c.tag_id)
            .join(
                BackgroundModel,
                BackgroundModel.id == background_tags.c.backgrounds_id,
            )
            .where(
                BackgroundModel.universe_id == universe_id,
                TagModel.type.in_(_BACKGROUND_TAG_TYPES),
            )
            .distinct()
            .order_by(TagModel.slug)
        )
        result = await self._session.scalars(stmt)
        return [TagRepository._to_domain(m) for m in result]

    @staticmethod
    def _to_domain(model: BackgroundModel) -> Background:
        return Background(
            id=model.id,
            universe_id=model.universe_id,
            slug=model.slug,
            description=model.description,
            asset_key=model.asset_key,
            sound_asset_key=model.sound.asset_key if model.sound else None,
            tags=[TagRepository._to_domain(t) for t in model.tags],
        )


class SoundRepository:
    """Репозиторий звуков на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_universe(self, universe_id: int) -> list[Sound]:
        stmt = (
            select(SoundModel)
            .where(SoundModel.universe_id == universe_id)
            .options(selectinload(SoundModel.tags))
            .order_by(SoundModel.id)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_by_id(self, sound_id: int) -> Sound | None:
        stmt = (
            select(SoundModel)
            .where(SoundModel.id == sound_id)
            .options(selectinload(SoundModel.tags))
        )
        model = await self._session.scalar(stmt)
        return self._to_domain(model) if model else None

    @staticmethod
    def _to_domain(model: SoundModel) -> Sound:
        return Sound(
            id=model.id,
            universe_id=model.universe_id,
            slug=model.slug,
            description=model.description,
            asset_key=model.asset_key,
            tags=[TagRepository._to_domain(t) for t in model.tags],
        )
