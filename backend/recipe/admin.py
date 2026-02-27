from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (
    BaseUser,
    Cart,
    Favorite,
    Follow,
    Ingredient,
    IngredientAmount,
    Recipe,
    Tag,
)


class BaseAdminWithRecipeMixin:
    list_display = ('recipe_count',)

    @admin.display(description='Рецепты')
    def recipe_count(self, instance):
        return instance.recipes.count()


@admin.register(BaseUser)
class BaseUserAdmin(UserAdmin, BaseAdminWithRecipeMixin):
    list_display = (
        'pk',
        'username',
        'email',
        'full_name',
        'subscription_count',
        'follower_count',
        *BaseAdminWithRecipeMixin.list_display,
        'image_preview',
    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            'Личная информация',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                    'avatar',
                    'image_preview',
                )
            },
        ),
        ('Права доступа', {'fields': ('is_active',)}),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)
    readonly_fields = ('image_preview',)

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @mark_safe
    @admin.display(description='Аватар')
    def image_preview(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" height="50"/>'
        return ''

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.followers.count()

    @admin.display(description='Подписчики')
    def follower_count(self, user):
        return user.authors.count()


@admin.register(Favorite, Cart)
class FavoriteAndCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(Ingredient)
class IngredientAdmin(BaseAdminWithRecipeMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'pk',
        'name',
        'measurement_unit',
        *BaseAdminWithRecipeMixin.list_display,
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    extra = 1
    autocomplete_fields = [
        'ingredient',
    ]
    readonly_fields = ('measurement_unit',)
    fields = ('ingredient', 'amount', 'measurement_unit')

    @admin.display(description='Единицы измерения')
    def measurement_unit(self, recipe):
        return recipe.ingredient.measurement_unit


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount', 'measurement_unit')
    list_filter = ('amount',)

    @admin.display(description='Единицы измерения')
    def measurement_unit(self, recipe):
        return recipe.ingredient.measurement_unit


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'count_favorites',
        'ingredients_list',
        'tags_list',
        'image_preview',
    )
    list_filter = ('author', 'tags')
    inlines = [IngredientAmountInline]
    fieldsets = (
        (
            'Основное',
            {
                'fields': (
                    'name',
                    'text',
                    'cooking_time',
                    'author',
                )
            },
        ),
        (
            'Изображение',
            {'fields': ('image', 'image_preview')},
        ),
        ('Теги и ингредиенты', {'fields': ('tags',)}),
    )
    readonly_fields = ('image_preview',)

    @admin.display(description='В избранном')
    def count_favorites(self, recipe):
        return recipe.favorites.count()

    @mark_safe
    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @mark_safe
    @admin.display(description='Ингредиенты')
    def ingredients_list(self, recipe):
        return '<br>'.join(
            f'{ingredient_amount.ingredient.name}, '
            f'{ingredient_amount.amount} '
            f'{ingredient_amount.ingredient.measurement_unit}'
            for ingredient_amount in recipe.ingredientamounts.all()
        )

    @admin.display(description='Картинка')
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="50" height="50"/>'
        return ''


@admin.register(Follow)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user__username', 'author__username')


@admin.register(Tag)
class TagAdmin(BaseAdminWithRecipeMixin, admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug',
        *BaseAdminWithRecipeMixin.list_display,
    )
    search_fields = ('name', 'slug')


admin.site.unregister(Group)
