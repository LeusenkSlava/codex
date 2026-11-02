from typing import Protocol

from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background, Sound, Universe


class UniverseRepositoryProtocol(Protocol):
    """Репозиторий вселенных."""

    async def search(
        self, query: str | None = None, offset: int = 0, limit: int = 20
    ) -> tuple[list[Universe], int]:
        """Страница вселенных и общее число вселенных по фильтру.

        :param query: подстрока для поиска по `title` без учёта регистра.
        :param offset: сколько вселенных пропустить.
        :param limit: размер страницы.
        :return: `(вселенные, всего найдено)`.
        """
        ...

    async def get(self, universe_id: int) -> Universe:
        """Вселенная по id.

        :param universe_id: id вселенной.
        :return: вселенная.
        """
        ...


class BackgroundRepositoryProtocol(Protocol):
    """Репозиторий задников."""

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        """Задники вселенной.

        :param universe_id: id вселенной.
        :return: задники с тегами и звуком, по возрастанию id.
        """
        ...

    async def get_by_universe_ids(self, universe_ids: list[int]) -> list[Background]:
        """Задники нескольких вселенных одной выборкой.

        :param universe_ids: id вселенных.
        :return: задники с тегами и звуком, сгруппированные по `universe_id`.
        """
        ...

    async def get_by_id(self, background_id: int) -> Background | None:
        """Задник по id.

        :param background_id: id задника.
        :return: задник с тегами и звуком или None.
        """
        ...

    async def get_tags_by_universe(self, universe_id: int) -> list[Tag]:
        """Теги задников вселенной (только `location` и `time_of_day`).

        :param universe_id: id вселенной.
        :return: теги без повторов, по slug.
        """
        ...


class SoundRepositoryProtocol(Protocol):
    """Репозиторий звуков."""

    async def get_by_universe(self, universe_id: int) -> list[Sound]:
        """Звуки вселенной.

        :param universe_id: id вселенной.
        :return: звуки с тегами, по возрастанию id.
        """
        ...

    async def get_by_id(self, sound_id: int) -> Sound | None:
        """Звук по id.

        :param sound_id: id звука.
        :return: звук с тегами или None.
        """
        ...
