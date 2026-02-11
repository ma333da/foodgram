from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    Tag,
    Follow,
    BaseUser
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorites', 'id')
    list_filter = ('author', 'name', 'tags')

    def count_favorites(self, obj):
        return obj.favorites.count()

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
    
class BaseUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
    )
    search_fields = ('username', 'email')
    ordering = ('username',)
    

class TagAdmin(admin.ModelAdmin): 
    
    list_display = ('pk', 'name', 'slug')

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs.annotate(recipes_count=Count("recipe", distinct=True))

    # @admin.display(description="Кол-во рецептов", ordering="recipes_count")
    
    # def recipes_count(self, obj):
    #     return obj.recipes_count

    
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Cart)
admin.site.register(Favorite)
admin.site.register(IngredientAmount)
admin.site.register(Tag, TagAdmin)
admin.site.register(Follow)
admin.site.register(BaseUser)