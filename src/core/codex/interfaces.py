from typing import Protocol

from src.core.codex.models.character import Character, Emotion, Outfit, Sprite
from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background, Universe


class UniverseRepositoryProtocol(Protocol):
    """Репозиторий вселенных."""

    async def all(self) -> list[Universe]:
        """Возвращает все вселенные.

        :return: список вселенных.
        """
        ...

    async def get(self, universe_id: int) -> Universe:
        """Возвращает вселенной по id.

        :return: вселенная.
        """
        ...


class CharacterRepositoryProtocol(Protocol):
    """Репозиторий персонажей."""

    async def get_by_universe(self, universe_id: int) -> list[Character]:
        """Возвращает всех персонажей вселенной.

        :param universe_id: id вселенной.
        :return: список персонажей с тегами.
        """
        ...


class SpriteRepositoryProtocol(Protocol):
    """Репозиторий спрайтов."""

    async def get_by_character(self, character_id: int) -> list[Sprite]:
        """Возвращает все спрайты персонажа.

        :param character_id: id персонажа.
        :return: список спрайтов с тегами.
        """
        ...

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Sprite]:
        """Возвращает спрайты персонажей

        :param character_ids: id персонажей.
        :return: словарь где клюс id персонажа.
        """
        ...


class OutfitRepositoryProtocol(Protocol):
    """Репозиторий одежды."""

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        """Возвращает всю одежду спрайта.

        :param sprite_id: id спрайта.
        :return: список одежды с тегами.
        """
        ...

    async def get_by_sprite_and_tag(
        self, sprite_id: int, tag_slug: str
    ) -> Outfit | None:
        """Возвращает одну одежду спрайта с указанным тегом.

        Если подходит несколько, возвращается одежда с наибольшим id.

        :param sprite_id: id спрайта.
        :param tag_slug: slug тега одежды.
        :return: одежда с тегами или None.
        """
        ...

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Возвращает уникальные outfit-теги всей одежды персонажа.

        :param character_id: id персонажа.
        :return: список тегов типа outfit_style без повторений.
        """
        ...


class EmotionRepositoryProtocol(Protocol):
    """Репозиторий эмоций."""

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        """Возвращает все эмоции персонажа по всем его спрайтам.

        :param character_id: id персонажа.
        :return: список эмоций с тегами.
        """
        ...

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Emotion]:
        """Возвращает все эмоции персонажа по всем его спрайтам.

        :param character_ids: список id персонажей.
        :return: список эмоций с тегами.
        """
        ...

    async def get_by_sprite(self, sprite_id: int) -> list[Emotion]:
        """Возвращает все эмоции спрайта.

        :param sprite_id: id спрайта.
        :return: список эмоций с тегами.
        """
        ...

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Возвращает уникальные emotion-теги всех эмоций персонажа.

        :param character_id: id персонажа.
        :return: список тегов типа emotion (с kind).
        """
        ...


class BackgroundRepositoryProtocol(Protocol):
    """Репозиторий задников."""

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        """Возвращает все задники вселенной.

        :param universe_id: id вселенной.
        :return: список задников с тегами.
        """
        ...


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
