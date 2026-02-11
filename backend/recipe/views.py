from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

from api.pagination import RecipePagination
from api.permissions import IsOwnerOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from .models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    Tag,
    Follow
)
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    FollowCreateSerializer,
    CropRecipeSerializer,
    FollowSerializer
)
from .utils import convert_txt

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
        return self.add_obj(Favorite, request.user, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_obj(Favorite, request.user, pk)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.add_obj(Cart, request.user, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_obj(Cart, request.user, pk)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def get_shopping_cart_ingredients(self, user):
        return (
            Cart.objects.filter(user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

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
        return convert_txt(ingredients)

    @staticmethod
    def add_obj(model, user, pk):
        recipe = Recipe.objects.filter(id=pk).first()
        if recipe is None:
            return Response(
                {'errors': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в список'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model.objects.create(user=user, recipe=recipe)
        serializer = CropRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        recipe = Recipe.objects.filter(id=pk).first()
        

        obj = model.objects.filter(user=user, recipe=recipe)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': 'Рецепт уже удален'},
            status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny, ]
    pagination_class = None

class CustomUserViewSet(UserViewSet):
    pagination_class = RecipePagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(BaseUser, pk=id)

        if request.method == 'POST':
            serializer = FollowCreateSerializer(
                data={'author': author.pk},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(
                FollowSerializer(
                    instance,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        subscription = Follow.objects.filter(user=request.user, author=author)
        if subscription.count() != 0:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
