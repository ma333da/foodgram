from django.core.exceptions import ValidationError

from foodgram.constants import PROHIBITED_USERNAME


def validate_username(value):
    if value == PROHIBITED_USERNAME:
        raise ValidationError(
            f"Использование имени {PROHIBITED_USERNAME}"
            "в качестве имени пользователя запрещено."
        )
    return value
