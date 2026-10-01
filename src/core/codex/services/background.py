from src.core.codex.interfaces import BackgroundRepositoryProtocol
from src.core.codex.models.universe import Background


class BackgroundService:
    """Сервис задников."""

    def __init__(self, repository: BackgroundRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        """Возвращает все задники вселенной.

        :param universe_id: id вселенной.
        :return: список задников с тегами.
        """
        return await self._repository.get_by_universe(universe_id)
