from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core import validators
from django.db import models

from .constants import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_USERNAME_LENGTH


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
        verbose_name='Логин пользователя',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        null=False,
        validators=[
            UnicodeUsernameValidator()
        ]
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
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
        verbose_name = 'Подписки',
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

    class Meta:
        abstract = True
        default_related_name = '%(class)s'


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH,
                            verbose_name='Название продукта')
    measurement_unit = models.CharField(max_length=MAX_NAME_LENGTH,
                                        verbose_name='Единица измерения')

    class Meta:
        ordering = ('-name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукта'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название',
        help_text='Введите название тега'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Идентификатор',
        help_text='Введите Идентификатор'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('pk', )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField(max_length=MAX_NAME_LENGTH,
                            verbose_name='Название')
    image = models.ImageField(upload_to='media/',
                              verbose_name='Картинка')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        verbose_name='Ингридиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное время приготовления 1 минута'),),
        verbose_name='Время приготовления')

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное количество ингридиентов 1'),),
        verbose_name='Количество',
    )

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Количество ингридиентов'
        verbose_name_plural = 'Количество ингридиентов'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique ingredients recipe')
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='favorite recipe for user')
        ]


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='personal user cart')
        ]
