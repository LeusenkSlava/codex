from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag
from src.outbound.database.models import TagModel


class TagRepository:
    """Репозиторий тегов на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_type(self, tag_type: TagType) -> list[Tag]:
        stmt = select(TagModel).where(TagModel.type == tag_type).order_by(TagModel.slug)
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result]

    async def get_by_slugs(self, slugs: list[str]) -> dict[str, Tag]:
        if not slugs:
            return {}

        stmt = select(TagModel).where(
            TagModel.type == TagType.EMOTION,
            TagModel.slug.in_(slugs),
        )
        result = await self._session.scalars(stmt)
        return {m.slug: self._to_domain(m) for m in result}

    async def get_by_slugs_and_types(
        self, slugs: list[str], tag_types: tuple[TagType, ...]
    ) -> dict[str, Tag]:
        if not slugs:
            return {}

        stmt = select(TagModel).where(
            TagModel.type.in_(tag_types),
            TagModel.slug.in_(slugs),
        )
        result = await self._session.scalars(stmt)
        return {m.slug: self._to_domain(m) for m in result}

    @staticmethod
    def _to_domain(model: TagModel) -> Tag:
        return Tag(
            id=model.id,
            type=model.type,
            slug=model.slug,
            name=model.name,
            kind=model.kind,
        )
