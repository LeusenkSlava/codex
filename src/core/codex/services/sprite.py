from src.core.codex.interfaces import SpriteRepositoryProtocol
from src.core.codex.models.character import Sprite


class SpriteService:
    """Сервис спрайтов."""

    def __init__(self, repository: SpriteRepositoryProtocol) -> None:
        self._repository = repository

    async def get_by_character(self, character_id: int) -> list[Sprite]:
        """Все спрайты персонажа.

        :param character_id: id персонажа.
        :return: спрайты с тегами, по возрастанию id.
        """
        return await self._repository.get_by_character(character_id)

    async def get_grouped(self, character_ids: list[int]) -> dict[int, list[Sprite]]:
        """Спрайты сразу нескольких персонажей.

        :param character_ids: id персонажей.
        :return: `character_id` → спрайты; у персонажа без спрайтов — пустой
            список.
        """
        sprites = await self._repository.get_by_character_ids(character_ids)

        grouped = {cid: [] for cid in character_ids}
        for model in sprites:
            grouped[model.character_id].append(model)

        return grouped
