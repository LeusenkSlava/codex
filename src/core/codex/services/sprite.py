from src.core.codex.interfaces import SpriteRepositoryProtocol
from src.core.codex.models.character import Sprite


class SpriteService:
    """Сервис спрайтов."""

    def __init__(self, repository: SpriteRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_character(self, character_id: int) -> list[Sprite]:
        """Возвращает все спрайты персонажа.

        :param character_id: id персонажа.
        :return: список спрайтов с тегами.
        """
        return await self._repository.get_by_character(character_id)
