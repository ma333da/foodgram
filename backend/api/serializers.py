from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer
from rest_framework import serializers

from recipe.constants import MIN_AMOUNT
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

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields, 'is_subscribed', 'avatar')
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request is not None
            or not request.user.is_anonymous
            and Follow.objects.filter(
                user=request.user, author=author
            ).exists()
        )


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

    def get_recipes(self, recipe):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        qs = Recipe.objects.filter(author=recipe.author)

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
    id = serializers.ReadOnlyField(source='ingredient.id')
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
        source='ingredientamount_set',
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
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return relation_model.objects.filter(user=user, recipe=recipe).exists()

    def get_is_favorited(self, favorite):
        return self._is_related(favorite, Favorite)

    def get_is_in_shopping_cart(self, cart):
        return self._is_related(cart, Cart)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not instance.image:
            rep['image'] = 'Нет изображения'
        return rep


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(write_only=True)
    tags = serializers.ListField(write_only=True)
    cooking_time = serializers.IntegerField(write_only=True)

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
        ingredients = self.initial_data.get('ingredients')
        image = self.initial_data.get('image')
        cooking_time = self.initial_data.get('cooking_time')

        if not image:
            raise serializers.ValidationError({'image': 'Нужна картинка.'})

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент для рецепта.'}
            )

        if not cooking_time:
            raise serializers.ValidationError(
                {'cooking_time': 'Обязательно укажите время приготовления.'}
            )
        elif cooking_time <= 0:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовления должно быть больше 0.'}
            )

        ingredient_counts = {}
        ingredient_ids = []

        for ingredient_item in ingredients:
            ingredient_id = ingredient_item.get('id')
            amount = ingredient_item.get('amount')

            if ingredient_id is None:
                raise serializers.ValidationError(
                    {'ingredients': 'У ингредиента отсутствует id.'}
                )
            ingredient_id_int = int(ingredient_id)
            ingredient_ids.append(ingredient_id_int)

            if ingredient_id_int in ingredient_counts:
                ingredient_counts[ingredient_id_int] += 1
            else:
                ingredient_counts[ingredient_id_int] = 1

            try:
                if int(amount) <= 0:
                    raise serializers.ValidationError(
                        {
                            'ingredients':
                                'Кол-во ингредиентов должно быть больше 0.'
                        }
                    )
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    {'ingredients': 'Кол-во продуктов должен быть числом.'}
                )
            existing_ids = set(
                Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                    'id', flat=True
                )
            )
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                {'ingredients': f'Продукты не найдены: {sorted(missing_ids)}'}
            )

        self.check_for_duplicates(ingredient_ids, 'ingridients', Ingredient)

        data['ingredients'] = ingredients
        tags_ids = self.initial_data.get('tags')
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
        tags_data = validated_data.pop('tags', [])
        recipe = super().create(validated_data)
        recipe.tags.set(set(tags_data))
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)
        instance.ingredientamounts.all().delete()
        self.create_ingredients(validated_data.get('ingredients'), instance)
        return instance

    def check_for_duplicates(self, items, field_name, model):
        if items != set(items):
            duplicate_items = {i for i in items if items.count(i) > 1}
            duplicate_names = model.objects.filter(
                id__in=duplicate_items
            ).values_list('name', flat=True)
            raise serializers.ValidationError(
                {field_name: f'Повторяющиеся {field_name}: {duplicate_names}'})
