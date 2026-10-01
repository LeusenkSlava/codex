from src.core.codex.interfaces import UniverseRepositoryProtocol
from src.core.codex.models.universe import Universe


class UniverseService:
    """Сервис вселенных."""

    def __init__(self, repository: UniverseRepositoryProtocol) -> None:
        self._repository = repository

    async def get_all(self) -> list[Universe]:
        """Возвращает все вселенные.

        :return: список вселенных.
        """
        return await self._repository.get_all()
