from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core import validators
from django.db import models

from .constants import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
    MAX_SECOND_NAME_LENGTH,
    MAX_SLUG_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_COOKING_TIME,
    MIN_NUM_OF_INGR,
)


class BaseUser(AbstractUser):
    email = models.EmailField(
        verbose_name='Почта', unique=True, max_length=MAX_EMAIL_LENGTH
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=MAX_FIRST_NAME_LENGTH
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=MAX_SECOND_NAME_LENGTH
    )
    username = models.CharField(
        verbose_name='Логин',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    avatar = models.ImageField(upload_to='media/', verbose_name='Аватарка')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчики',
    )
    author = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Авторы',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    def __str__(self):
        return f'{self.user}: {self.recipe}'

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_%(class)s_user_recipe'
            )
        ]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME_LENGTH, verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ('-name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='уникальный продукт'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Название',
        help_text='Введите название тега',
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        verbose_name='Идентификатор',
        help_text='Введите Идентификатор',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME_LENGTH, verbose_name='Название'
    )
    image = models.ImageField(upload_to='media/', verbose_name='Картинка')

    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientAmount', verbose_name='Продукты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        validators=(validators.MinValueValidator(MIN_COOKING_TIME),),
        verbose_name='Время (мин)',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = '%(class)ss'


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Продукт'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                MIN_NUM_OF_INGR,
                message=f'Минимальное количество продуктов {MIN_NUM_OF_INGR}',
            ),
        ),
        verbose_name='Количество',
    )

    def __str__(self):
        return f'{self.recipe}: {self.ingredient} - {self.amount}'

    class Meta:
        ordering = ('ingredient',)
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_%(class)s_user_recipe',
            )
        ]


class Favorite(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = '%(class)ss'


class Cart(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        default_related_name = '%(class)ss'
