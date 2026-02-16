from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import (BaseUser, Cart, Favorite, Follow, Ingredient,
                     IngredientAmount, Recipe, Tag)


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
    
    @admin.display(description='Количество рецептов')
    def recipe_count(self, user):
        return user.recipes.count()

    @mark_safe
    def avatar(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" width="50" height="50" />'
            )
        return '<p>Нет аватара</p>'

    @admin.display(description='Количество подписок')
    def subscription_count(self, user):
        return user.followers.count()

    @admin.display(description='Количество подписчиков')
    def follower_count(self, user):
        return user.authors.count()


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit', 'number_of_recipes')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')

    def number_of_recipes(self, ingridient):
        return ingridient.ingredients_amount.count()

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

    @admin.display(description='В избранном')
    def count_favorites(self, recipe):
        return recipe.favorite_set.count()

    @admin.display(description='Новое описание')
    def ingredients_list(self, recipe):
        return '<br>'.join(
            ingredient.name for ingredient in recipe.ingredients.all()
        )

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

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

    @admin.display(description='Количество рецептов')
    def recipe_count(self, tag):
        return tag.recipe_set.count()



admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Follow, SubscriptionAdmin)
admin.site.register(BaseUser, BaseUserAdmin)
