from src.core.codex.interfaces import UniverseRepositoryProtocol
from src.core.codex.models.universe import Universe


class UniverseService:
    """Сервис вселенных."""

    def __init__(self, repository: UniverseRepositoryProtocol) -> None:
        self._repository = repository

    async def search(
        self, query: str | None = None, offset: int = 0, limit: int = 20
    ) -> tuple[list[Universe], int]:
        """Возвращает страницу вселенных и их общее число.

        :param query: необязательная подстрока для поиска по названию (title).
        :param offset: сколько вселенных пропустить.
        :param limit: максимальное число вселенных в странице.
        :return: кортеж ``(вселенные, всего найдено)``.
        """
        return await self._repository.search(query=query, offset=offset, limit=limit)

    async def get(self, universe_id: int) -> Universe:
        """Возвращает вселенной по id.

        :return: вселенная.
        """
        return await self._repository.get(universe_id)
