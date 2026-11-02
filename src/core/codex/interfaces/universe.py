from typing import Protocol

from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background, Sound, Universe


class UniverseRepositoryProtocol(Protocol):
    """Репозиторий вселенных."""

    async def search(
        self, query: str | None = None, offset: int = 0, limit: int = 20
    ) -> tuple[list[Universe], int]:
        """Возвращает страницу вселенных и их общее число.

        :param query: необязательная подстрока для поиска по названию (title).
        :param offset: сколько вселенных пропустить.
        :param limit: максимальное число вселенных в странице.
        :return: кортеж ``(вселенные, всего найдено)``.
        """
        ...

    async def get(self, universe_id: int) -> Universe:
        """Возвращает вселенной по id.

        :return: вселенная.
        """
        ...


class BackgroundRepositoryProtocol(Protocol):
    """Репозиторий задников."""

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        """Возвращает все задники вселенной.

        :param universe_id: id вселенной.
        :return: список задников с тегами.
        """
        ...

    async def get_by_universe_ids(self, universe_ids: list[int]) -> list[Background]:
        """Возвращает задники нескольких вселенных одной выборкой.

        :param universe_ids: id вселенных.
        :return: список задников с тегами.
        """
        ...

    async def get_by_id(self, background_id: int) -> Background | None:
        """Возвращает задник по id.

        :param background_id: id задника.
        :return: задник с тегами или None.
        """
        ...

    async def get_tags_by_universe(self, universe_id: int) -> list[Tag]:
        """Возвращает уникальные location- и time_of_day-теги задников вселенной.

        :param universe_id: id вселенной.
        :return: список тегов типов location и time_of_day без повторений.
        """
        ...


class SoundRepositoryProtocol(Protocol):
    """Репозиторий звуков."""

    async def get_by_universe(self, universe_id: int) -> list[Sound]:
        """Возвращает все звуки вселенной.

        :param universe_id: id вселенной.
        :return: список звуков с тегами.
        """
        ...

    async def get_by_id(self, sound_id: int) -> Sound | None:
        """Возвращает звук по id.

        :param sound_id: id звука.
        :return: звук с тегами или None.
        """
        ...
