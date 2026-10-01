from enum import StrEnum


class TagType(StrEnum):
    """Тип тега"""

    EMOTION = "emotion"  # sprite: neutral, happy, sad, angry, ...
    OUTFIT_STYLE = "outfit_style"  # sprite: casual, formal, swimsuit, ... (доп. к текстовому outfit)
    LOCATION = "location"  # background: площадь, столовая, пляж, ...
    TIME_OF_DAY = "time_of_day"  # background: morning, day, evening, night
    ARCHETYPE = "archetype"  # character: tsundere, kuudere, genki, ...
