from enum import StrEnum


class Gender(StrEnum):
    """Пол персонажа."""

    MALE = "male"
    FEMALE = "female"


class TagType(StrEnum):
    """Тип тега — определяет, к каким сущностям он привязан."""

    EMOTION = "emotion"  # спрайт: facial-слой
    OUTFIT_STYLE = "outfit_style"  # одежда: стиль одежды
    LOCATION = "location"  # задник: сама локация
    TIME_OF_DAY = "time_of_day"  # задник: время суток
    ARCHETYPE = "archetype"  # персонаж: tsundere, kuudere, genki, ...
    MUSIC = "music"  # звук: музыка
    SFX = "sfx"  # звук: эффекты


class TagKind(StrEnum):
    """Роль тега внутри его типа.

    Значим для `emotion`, `outfit_style`, `location` и `time_of_day`: у тега
    такой сущности может быть один `base` и 0..N `modifier` — по ним идёт
    подбор. У остальных типов `kind` не заполняется.
    """

    BASE = "base"
    MODIFIER = "modifier"
