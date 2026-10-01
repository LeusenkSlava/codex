from src.core.codex.interfaces import CharacterRepositoryProtocol
from src.core.codex.models.character import Character


class CharacterService:
    """Сервис персонажей."""

    def __init__(self, repository: CharacterRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_universe(self, universe_id: int) -> list[Character]:
        """Возвращает всех персонажей вселенной.

        :param universe_id: id вселенной.
        :return: список персонажей с тегами.
        """
        return await self._repository.get_by_universe(universe_id)
