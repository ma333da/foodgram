from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Sum
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recipe.models import (Cart, Favorite, Follow, Ingredient,
                           IngredientAmount, Recipe, Tag)

from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (CropRecipeSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          TagSerializer)
from .utils import generate_text

BaseUser = get_user_model()


class IngredientsViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = RecipePagination
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.all().select_related('author')
        if user.is_authenticated:
            is_favorite_annotation = Exists(
                Favorite.objects.filter(
                    user=user,
                    recipe=OuterRef('pk')
                )
            )
            is_in_shopping_cart_annotation = Exists(
                Cart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk')
                )
            )
            queryset = queryset.annotate(
                is_favorited=is_favorite_annotation,
                is_in_shopping_cart=is_in_shopping_cart_annotation
            )

            return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.add_recipe(Favorite, request.user, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_recipe(Favorite, request.user, pk)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.add_recipe(Cart, request.user, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_recipe(Cart, request.user, pk)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientAmount.objects
            .filter(recipe__cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(ingredient_total=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = (Cart.objects.filter(author=request.user))
        return generate_text(ingredients, recipes)

    @staticmethod
    def add_recipe(model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)

        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в список'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model.objects.create(user=user, recipe=recipe)
        return Response(
            CropRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete_recipe(self, model, user, pk):
        get_object_or_404(Recipe, id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny, ]
    pagination_class = None


class FoodgramUserViewSet(UserViewSet):
    pagination_class = RecipePagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(BaseUser, pk=id)
        user = request.user
        if request.method == 'POST':
            if user == author:
                raise ValidationError('Нельзя подписаться на самого себя!')
            follow_obj, created = Follow.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                raise ValidationError(
                    f'Вы уже подписаны на пользователя {user}!'
                )
            return Response(
                FollowSerializer(follow_obj).data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(Follow, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = user.subscriptions.all()
        pages = self.paginate_queryset(queryset)
        response_data = [
            {'user': follow.user.pk, 'author': follow.author.pk}
            for follow in pages
        ]
        return self.get_paginated_response(response_data)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = self._generate_recipe_short_link(request, recipe)
        return Response({'short-link': short_link})

    def _generate_recipe_short_link(self, request, recipe):
        return request.build_absolute_uri(f'/s/{recipe.id}')
