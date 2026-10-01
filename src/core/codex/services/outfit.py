from src.core.codex.interfaces import OutfitRepositoryProtocol
from src.core.codex.models.character import Outfit


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
