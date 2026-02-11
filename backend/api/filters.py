from django_filters.rest_framework import FilterSet, filters

from ..recipe.models import BaseUser, Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class TagFilter(FilterSet):
    author = filters.ModelChoiceFilter(queryset=BaseUser.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(users_favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._apply_shopping_cart_filter(queryset, value)

    def filter_is_favorited(self, queryset, name, value):
        return self._apply_favorites_filter(queryset, value)

    def _apply_shopping_cart_filter(self, queryset, value):
        user = self.request.user

        if not value:
            return queryset

        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(cart__user=user)

    def _apply_favorites_filter(self, queryset, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset
