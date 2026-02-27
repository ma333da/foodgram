from datetime import date
import locale

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django.template.loader import render_to_string
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recipe.models import (
    Cart,
    Favorite,
    Follow,
    Ingredient,
    IngredientAmount,
    Recipe,
    Tag,
)

from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CropRecipeSerializer,
    FollowersSerializer,
    FoodgramUserSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

BaseUser = get_user_model()


class IngredientsViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Recipe.objects.all().select_related('author').order_by('-id')
        )

        if user.is_authenticated:
            is_favorite_annotation = Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
            )
            is_in_shopping_cart_annotation = Exists(
                Cart.objects.filter(user=user, recipe=OuterRef('pk'))
            )
            queryset = queryset.annotate(
                is_favorited=is_favorite_annotation,
                is_in_shopping_cart=is_in_shopping_cart_annotation,
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.add_recipe_to_collection(Favorite, request.user, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_recipe_from_collection(Favorite, request.user, pk)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.add_recipe_to_collection(Cart, request.user, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_recipe_from_collection(Cart, request.user, pk)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        shop_list = (
            IngredientAmount.objects.filter(recipe__carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(ingredient_total=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = Recipe.objects.filter(carts__user=request.user).distinct()
        return FileResponse(
            render_to_string(
                'shopping_list.txt',
                {
                    'date': date.today().strftime('%d %B %Y'),
                    'shop_list': shop_list,
                    'recipes': recipes,
                },
            ),
            content_type='text/plain',
            filename='cart.txt',
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError({'error': f'Рецепт c id {pk} не найден'})
        return Response({'short-link': request.build_absolute_uri(f'/s/{pk}')})

    @staticmethod
    def add_recipe_to_collection(model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        _, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            vebose_name = model._meta.verbose_name
            raise ValidationError(
                {
                    'errors':
                    f'Рецепт {recipe.name} уже добавлен в список {vebose_name}'
                }
            )
        return Response(
            CropRecipeSerializer(recipe).data, status=status.HTTP_201_CREATED
        )

    def delete_recipe_from_collection(self, model, user, pk):
        model.objects.filter(user=user, recipe_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [
        AllowAny,
    ]
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
        if request.method == 'DELETE':
            follow = get_object_or_404(Follow, user=user, author=author)
            follow.delete()
            return Response(status=status.HTTP_200_OK)
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя!')
        _, created = Follow.objects.get_or_create(user=user, author=author)
        if not created:
            raise ValidationError(
                f'Вы уже подписаны на пользователя {author.username}!'
            )
        return Response(
            FollowersSerializer(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = BaseUser.objects.filter(authors__user=request.user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = FollowersSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowersSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = FoodgramUserSerializer(
            user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user.refresh_from_db()
        avatar_url = None
        if user.avatar:
            avatar_url = request.build_absolute_uri(user.avatar.url)
        return Response(
            {'avatar': avatar_url},
            status=status.HTTP_200_OK,
        )
