from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
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


class BaseUserAdmin(UserAdmin):
    list_display = (
        'pk',
        'username',
        'email',
        'full_name',
        'is_staff',
        'recipe_count',
        'avatar',
        'subscription_count',
        'follower_count',
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

    def full_name(self, base_user):
        return f'{base_user.first_name} {base_user.last_name}'

    full_name.short_description = 'ФИО'

    def recipe_count(self, base_user):
        return base_user.recipes.count()

    recipe_count.short_description = 'Количество рецептов'

    @mark_safe
    def avatar(self, base_user):
        if base_user.avatar:
            return (
                f'<img src="{base_user.avatar.url}" width="50" height="50" />'
            )
        return '<p>Нет аватара</p>'

    def subscription_count(self, obj):
        return obj.followers.count()

    subscription_count.short_description = 'Количество подписок'

    def follower_count(self, obj):
        return obj.authors.count()

    follower_count.short_description = 'Количество подписчиков'


class CartAdmin(admin.ModelAdmin):
    pass


class FavoriteAdmin(admin.ModelAdmin):
    pass


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit', 'number_of_recipes')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')

    def number_of_recipes(self, ingridient):
        return ingridient.ingredientamount_set.count()

    number_of_recipes.short_description = 'Число рецептов'


class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')


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

    def count_favorites(self, recipe):
        return recipe.favorite_set.count()

    count_favorites.short_description = 'В избранном'

    def ingredients_list(self, recipe):
        return '\n '.join(
            [ingredient.name for ingredient in recipe.ingredients.all()]
        )

    ingredients_list.short_description = 'Продукты'

    def tags_list(self, recipe):
        return ', '.join([tag.name for tag in recipe.tags.all()])

    tags_list.short_description = 'Теги'

    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="50" height="50"/>'
        return 'Нет изображения'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user__username', 'author__username')


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'recipe_count')

    def recipe_count(self, obj):
        return obj.recipe_set.count()

    recipe_count.short_description = 'Количество рецептов'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Follow, SubscriptionAdmin)
admin.site.register(BaseUser, BaseUserAdmin)
