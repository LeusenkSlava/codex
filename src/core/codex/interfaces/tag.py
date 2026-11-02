from typing import Protocol

from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag


class TagRepositoryProtocol(Protocol):
    """Репозиторий тегов."""

    async def get_by_type(self, tag_type: TagType) -> list[Tag]:
        """Все теги указанного типа.

        :param tag_type: тип тега.
        :return: теги, по slug.
        """
        ...

    async def get_by_slugs(self, slugs: list[str]) -> dict[str, Tag]:
        """Теги `emotion` по slug'ам.

        :param slugs: slug'и тегов `emotion`.
        :return: slug → тег; ненайденные slug'и в словарь не попадают.
        """
        ...

    async def get_by_slugs_and_types(
        self, slugs: list[str], tag_types: tuple[TagType, ...]
    ) -> dict[str, Tag]:
        """Теги указанных типов по slug'ам.

        :param slugs: slug'и тегов.
        :param tag_types: допустимые типы тегов.
        :return: slug → тег; теги других типов в словарь не попадают.
        """
        ...
