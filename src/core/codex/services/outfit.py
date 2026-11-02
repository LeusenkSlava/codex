from src.core.codex.interfaces import OutfitRepositoryProtocol
from src.core.codex.models.character import Outfit
from src.core.codex.models.tag import Tag


class OutfitService:
    """Сервис одежды."""

    def __init__(self, repository: OutfitRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        """Вся одежда спрайта.

        :param sprite_id: id спрайта.
        :return: одежда с тегами, по возрастанию id.
        """
        return await self._repository.get_by_sprite(sprite_id)

    async def match(self, sprite_id: int, tag_slug: str) -> Outfit | None:
        """Одежда спрайта по тегу `outfit_style`.

        При нескольких совпадениях берётся одежда с большим `id`.

        :param sprite_id: id спрайта.
        :param tag_slug: slug тега `outfit_style`.
        :return: одежда с тегами или None, если ничего не подошло.
        """
        return await self._repository.get_by_sprite_and_tag(sprite_id, tag_slug)

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Теги `outfit_style` всей одежды персонажа.

        :param character_id: id персонажа.
        :return: теги без повторов, по slug.
        """
        return await self._repository.get_tags_by_character(character_id)
