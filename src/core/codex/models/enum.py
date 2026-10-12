from enum import StrEnum


class TagType(StrEnum):
    """Тип тега"""

    EMOTION = "emotion"  # sprite: neutral, happy, sad, angry, ...
    OUTFIT_STYLE = "outfit_style"  # sprite: casual, formal, swimsuit, ... (доп. к текстовому outfit)
    LOCATION = "location"  # background: площадь, столовая, пляж, ...
    TIME_OF_DAY = "time_of_day"  # background: morning, day, evening, night
    ARCHETYPE = "archetype"  # character: tsundere, kuudere, genki, ...
    MUSIC = "music"  # sound: фоновая музыка (calm, battle, sad, ...)
    SFX = "sfx"  # sound: звуковые эффекты (дождь, выстрел, шаги, ...)


class TagKind(StrEnum):
    """Роль тега внутри типа emotion.

    Каждой эмоции-спрайту вешается ровно один base и 0..N modifier.
    """

    BASE = "base"  # обязательная, одна на реплику
    MODIFIER = "modifier"  # необязательные уточнения
