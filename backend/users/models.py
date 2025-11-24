from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from users.validators import validate_username

from foodgram.constants import (MAX_EMAIL_LENGTH, MAX_NAME_LENGTH,
                                MAX_USERNAME_LENGTH)


class BaseUser(AbstractUser):
    email = models.EmailField(
        verbose_name='Почта',
        unique=True,
        max_length=MAX_EMAIL_LENGTH
    )
    first_name = models.CharField(
        verbose_name='Имя',
        null=False,
        max_length=MAX_NAME_LENGTH
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        null=False,
        max_length=MAX_NAME_LENGTH
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        null=False,
        validators=[
            validate_username,
            UnicodeUsernameValidator()
        ]
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписки',
        verbose_name_plural = 'Подписки'
