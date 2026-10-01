from src.core.codex.interfaces import EmotionRepositoryProtocol
from src.core.codex.models.character import Emotion


class EmotionService:
    """Сервис эмоций."""

    def __init__(self, repository: EmotionRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        """Возвращает все эмоции персонажа по всем его спрайтам.

        :param character_id: id персонажа.
        :return: список эмоций с тегами.
        """
        return await self._repository.get_by_character(character_id)
