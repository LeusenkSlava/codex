from src.core.codex.interfaces import OutfitRepositoryProtocol
from src.core.codex.models.character import Outfit
from src.core.codex.models.tag import Tag


class OutfitService:
    """Сервис одежды."""

    def __init__(self, repository: OutfitRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        """Возвращает всю одежду спрайта.

        :param sprite_id: id спрайта.
        :return: список одежды с тегами.
        """
        return await self._repository.get_by_sprite(sprite_id)

    async def match(self, sprite_id: int, tag_slug: str) -> Outfit | None:
        """Возвращает одну одежду спрайта по тегу.

        Если под несколько вариантов, выбирается одежда с наибольшим id.

        :param sprite_id: id спрайта.
        :param tag_slug: slug тега одежды.
        :return: одежда с тегами или None.
        """
        return await self._repository.get_by_sprite_and_tag(sprite_id, tag_slug)

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        """Возвращает уникальные outfit-теги всей одежды персонажа.

        :param character_id: id персонажа.
        :return: список тегов типа outfit_style без повторений.
        """
        return await self._repository.get_tags_by_character(character_id)
