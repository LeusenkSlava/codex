from typing import Protocol

from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag


class TagRepositoryProtocol(Protocol):
    """Репозиторий тегов."""

    async def get_by_type(self, tag_type: TagType) -> list[Tag]:
        """Возвращает все теги указанного типа.

        :param tag_type: тип тега.
        :return: список тегов.
        """
        ...

    async def get_by_slugs(self, slugs: list[str]) -> dict[str, Tag]:
        """Возвращает emotion-теги по slug'ам.

        :param slugs: slug'и тегов типа emotion.
        :return: словарь slug -> тег.
        """
        ...

    async def get_by_slugs_and_types(
        self, slugs: list[str], tag_types: tuple[TagType, ...]
    ) -> dict[str, Tag]:
        """Возвращает теги указанных типов по slug'ам.

        :param slugs: slug'и тегов.
        :param tag_types: допустимые типы тегов.
        :return: словарь slug -> тег.
        """
        ...
