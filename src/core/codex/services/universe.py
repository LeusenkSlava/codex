from src.core.codex.interfaces import UniverseRepositoryProtocol
from src.core.codex.models.universe import Universe


class UniverseService:
    """Сервис вселенных."""

    def __init__(self, repository: UniverseRepositoryProtocol) -> None:
        self._repository = repository

    async def search(
        self, query: str | None = None, offset: int = 0, limit: int = 20
    ) -> tuple[list[Universe], int]:
        """Страница вселенных и общее число вселенных по фильтру.

        :param query: подстрока для поиска по `title` без учёта регистра.
        :param offset: сколько вселенных пропустить.
        :param limit: размер страницы.
        :return: `(вселенные, всего найдено)`.
        """
        return await self._repository.search(query=query, offset=offset, limit=limit)

    async def get(self, universe_id: int) -> Universe:
        """Вселенная по id.

        :param universe_id: id вселенной.
        :return: вселенная.
        """
        return await self._repository.get(universe_id)
