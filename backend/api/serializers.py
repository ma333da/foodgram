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
        fields = (*UserSerializer.Meta.fields, 'is_subscribed')
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


class FollowSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='user.recipes.count()')

    class Meta:
        model = User
        fields = (
            *FoodgramUserSerializer.Meta.fields,
            'recipes',
            'recipes_count'
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

    def get_recipes_count(self, recipe):
        return recipe.objects.filter(author=recipe.author).count()


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
        validators=[
            MinValueValidator(
                {MIN_AMOUNT},
                message=f'Количество должно быть не менее {MIN_AMOUNT}'
            )
        ]
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
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

    def _is_related(self, recipe, relation_model):
        annotated = getattr(recipe, relation_model.__name__.lower(), None)
        if annotated is not None:
            return bool(annotated)

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return relation_model.objects.filter(
            user=user,
            recipe=recipe
        ).exists()

    def get_is_favorited(self, favorite):
        return self._is_related(favorite, Favorite)

    def get_is_in_shopping_cart(self, cart):
        return self._is_related(cart, Cart)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not instance.image:
            rep['image'] = 'Нет изображения'
        return rep

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        image = self.initial_data.get('image')

        if not image:
            raise serializers.ValidationError({'image': 'Нужна картинка.'})

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент для рецепта.'}
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

        duplicates = [
            ingredient_id
            for ingredient_id, count in ingredient_counts.items()
            if count > 1
        ]

        if duplicates:
            duplicate_names = Ingredient.objects.filter(
                id__in=duplicates
            ).values_list(
                'name', flat=True
            )
            raise serializers.ValidationError(
                {
                    'ingredients': f'Продукты должны быть уникальными. '
                    f'Повторяются: {duplicate_names}.'
                }
            )

        data['ingredients'] = ingredients
        tags_ids = self.initial_data.get('tags')

        if len(tags_ids) != len(set(tags_ids)):
            raise serializers.ValidationError(
                {'tags': 'Повторяющиеся теги не допускаются.'}
            )

        data['tags_ids'] = tags_ids
        return data

    def create_ingredients(self, ingredients, recipe):
        IngredientAmount.objects.bulk_create(
            [
                IngredientAmount(
                    recipe=recipe,
                    ingredient_id=ingredient.get('id'),
                    amount=ingredient.get('amount'),
                )
                for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(set(self.initial_data.get('tags')))
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)
        IngredientAmount.objects.filter(recipe=instance).all().delete()
        self.create_ingredients(validated_data.get('ingredients'), instance)
        instance.save()
        return instance
