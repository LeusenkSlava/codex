from typing import Protocol

from src.core.codex.models.character import Character, Emotion, Outfit, Sprite
from src.core.codex.models.enum import TagType
from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background, Universe


class UniverseRepositoryProtocol(Protocol):
    """Репозиторий вселенных."""

    async def get_all(self) -> list[Universe]:
        """Возвращает все вселенные.

        :return: список вселенных.
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


class OutfitRepositoryProtocol(Protocol):
    """Репозиторий одежды."""

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        """Возвращает всю одежду спрайта.

        :param sprite_id: id спрайта.
        :return: список одежды с тегами.
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

    async def get_by_sprite(self, sprite_id: int) -> list[Emotion]:
        """Возвращает все эмоции спрайта.

        :param sprite_id: id спрайта.
        :return: список эмоций с тегами.
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
