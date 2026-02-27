from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipe.constants import MIN_AMOUNT, MIN_COOKING_TIME
from recipe.models import (
    Cart,
    Favorite,
    Follow,
    Ingredient,
    IngredientAmount,
    Recipe,
    Tag,
)

User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields, 'is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, author=author).exists()


class CropRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.pk')
    author = serializers.ReadOnlyField(source='author.pk')

    class Meta:
        model = Follow
        fields = ['user', 'author']


class FollowersSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            *FoodgramUserSerializer.Meta.fields,
            'recipes',
            'recipes_count',
        )
        read_only_fields = fields

    def get_recipes(self, author):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        qs = Recipe.objects.filter(author=author)

        if limit:
            try:
                qs = qs[: int(limit)]
            except (TypeError, ValueError):
                pass
        return CropRecipeSerializer(qs, many=True).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(validators=[MinValueValidator(MIN_AMOUNT)])
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(MIN_AMOUNT)]
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = FoodgramUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientamounts',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def _is_related(self, recipe, relation_model):
        annotated = getattr(recipe, relation_model.__name__.lower(), None)
        if annotated is not None:
            return bool(annotated)

        request = self.context.get('request')
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return relation_model.objects.filter(user=user, recipe=recipe).exists()

    def get_is_favorited(self, favorite):
        return self._is_related(favorite, Favorite)

    def get_is_in_shopping_cart(self, cart):
        return self._is_related(cart, Cart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, write_only=True
    )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        image = data.get('image')
        is_create = self.instance is None

        if is_create and not image:
            raise serializers.ValidationError({'image': 'Нужна картинка.'})

        if ingredients is not None:
            if is_create and not ingredients:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        'Нужен хотя бы один ингредиент для рецепта.'
                    }
                )
            self.check_for_duplicates(
                [ingredient_item['id'] for ingredient_item in ingredients],
                'ingredients',
                Ingredient,
            )
        tags_ids = self.initial_data.get('tags')
        if tags_ids is not None:
            self.check_for_duplicates(tags_ids, 'tags', Tag)
        return data

    def create_ingredients(self, ingredients, recipe):
        IngredientAmount.objects.bulk_create(
            IngredientAmount(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(set(tags_data))
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags_data)
        ingredients_data = validated_data.pop('ingredients')
        instance.ingredientamounts.all().delete()
        self.create_ingredients(ingredients_data, instance)
        return super().update(instance, validated_data)

    def check_for_duplicates(self, items, field_name, model):
        if len(items) != len(set(items)):
            duplicate_items = {i for i in items if items.count(i) > 1}
            duplicate_names = model.objects.filter(
                id__in=duplicate_items
            ).values_list('name', flat=True)
            raise serializers.ValidationError(
                {field_name: f'Повторяющиеся {field_name}: {duplicate_names}'}
            )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
