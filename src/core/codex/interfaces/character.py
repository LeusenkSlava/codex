from typing import Protocol

from src.core.codex.models.character import Character, Emotion, Outfit, Sprite
from src.core.codex.models.tag import Tag


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

    async def get_by_id(self, sprite_id: int) -> Sprite | None:
        """Возвращает спрайт по id.

        :param sprite_id: id спрайта.
        :return: спрайт с тегами или None.
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

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Outfit]:
        """Возвращает одежду нескольких персонажей одной выборкой.

        :param character_ids: id персонажей.
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

    async def get_by_character_and_tag(
        self, character_id: int, tag_slug: str
    ) -> list[Outfit]:
        """Возвращает всю одежду персонажа с указанным тегом.

        Сортировка — по убыванию id одежды.

        :param character_id: id персонажа.
        :param tag_slug: slug тега одежды.
        :return: список одежды с тегами.
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
