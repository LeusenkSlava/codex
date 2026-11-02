from typing import Protocol

from src.core.codex.models.character import Character, Emotion, Outfit, Sprite
from src.core.codex.models.tag import Tag


class CharacterRepositoryProtocol(Protocol):
    """Репозиторий персонажей."""

    async def get_by_universe(self, universe_id: int) -> list[Character]:
        """Персонажи вселенной.

        :param universe_id: id вселенной.
        :return: персонажи с тегами, по возрастанию id.
        """
        ...


class SpriteRepositoryProtocol(Protocol):
    """Репозиторий спрайтов."""

    async def get_by_character(self, character_id: int) -> list[Sprite]:
        """Спрайты персонажа.

        :param character_id: id персонажа.
        :return: спрайты с тегами, по возрастанию id.
        """
        ...

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Sprite]:
        """Спрайты нескольких персонажей одной выборкой.

        :param character_ids: id персонажей.
        :return: спрайты с тегами, сгруппированные по `character_id`.
        """
        ...

    async def get_by_id(self, sprite_id: int) -> Sprite | None:
        """Спрайт по id.

        :param sprite_id: id спрайта.
        :return: спрайт с тегами или None.
        """
        ...


class OutfitRepositoryProtocol(Protocol):
    """Репозиторий одежды."""

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        """Одежда спрайта.

        :param sprite_id: id спрайта.
        :return: одежда с тегами, по возрастанию id.
        """
        ...

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Outfit]:
        """Одежда нескольких персонажей одной выборкой.

        :param character_ids: id персонажей.
        :return: одежда с тегами, сгруппированная по персонажу.
        """
        ...

    async def get_by_sprite_and_tag(
        self, sprite_id: int, tag_slug: str
    ) -> Outfit | None:
        """Одна одежда спрайта с указанным тегом `outfit_style`.

        При нескольких совпадениях берётся одежда с большим `id`.

        :param sprite_id: id спрайта.
        :param tag_slug: slug тега `outfit_style`.
        :return: одежда с тегами или None.
        """
        ...

    async def get_by_character_and_tag(
        self,
        character_id: int,
        tag_slug: str,
        *,
        include_tags: bool = True,
    ) -> list[Outfit]:
        """Вся одежда персонажа с указанным тегом `outfit_style`.

        :param character_id: id персонажа.
        :param tag_slug: slug тега `outfit_style`.
        :param include_tags: загружать ли теги одежды. Подбору визуала теги не
            нужны — ``False`` экономит запрос.
        :return: одежда по убыванию id (с тегами или с пустым ``tags`` при
            ``include_tags=False``).
        """
        ...

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Теги `outfit_style` всей одежды персонажа.

        :param character_id: id персонажа.
        :return: теги без повторов, по slug.
        """
        ...


class EmotionRepositoryProtocol(Protocol):
    """Репозиторий эмоций."""

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        """Все эмоции персонажа по всем его спрайтам.

        :param character_id: id персонажа.
        :return: эмоции с тегами и `character_id`, по возрастанию id.
        """
        ...

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Emotion]:
        """Эмоции нескольких персонажей одной выборкой.

        :param character_ids: id персонажей.
        :return: эмоции с тегами и `character_id`, по возрастанию id.
        """
        ...

    async def get_by_sprite(self, sprite_id: int) -> list[Emotion]:
        """Эмоции спрайта.

        :param sprite_id: id спрайта.
        :return: эмоции с тегами, по возрастанию id.
        """
        ...

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Теги `emotion` всех эмоций персонажа.

        :param character_id: id персонажа.
        :return: теги без повторов (с `kind`), по slug.
        """
        ...
