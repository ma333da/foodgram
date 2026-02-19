from django.contrib import admin
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


class BaseAdminWithRecipeCount(admin.ModelAdmin):
    list_display = ('recipe_count',)

    @admin.display(description='Рецепты')
    def recipe_count(self, instance):
        return instance.recipes.count()


@admin.register(BaseUser)
class BaseUserAdmin(BaseAdminWithRecipeCount):
    list_display = (
        'pk',
        'username',
        'email',
        'full_name',
        'is_staff',
        *BaseAdminWithRecipeCount.list_display,
        'avatar',
        'subscription_count',
        'follower_count',
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @mark_safe
    def avatar(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" height="50" />'
        return '<p></p>'

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.followers.count()

    @admin.display(description='Подписчики')
    def follower_count(self, user):
        return user.authors.count()


@admin.register(Favorite, Cart)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Ingredient)
class IngredientAdmin(BaseAdminWithRecipeCount):
    list_display = (
        'pk',
        'name',
        'measurement_unit',
        *BaseAdminWithRecipeCount.list_display,
    )
    search_fields = ('name', 'measurement_unit')


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')


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
            (
                (
                    f"""{ingredient_amount.ingredient.name}',
                ({ingredient_amount.amount}
                '{ingredient_amount.ingredient.measurement_unit})"""
                )
                for ingredient_amount in recipe.ingredientamounts.all()
            )
        )

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
class TagAdmin(BaseAdminWithRecipeCount):
    list_display = (
        'pk',
        'name',
        'slug',
        *BaseAdminWithRecipeCount.list_display,
    )
    search_fields = ('name', 'slug')
