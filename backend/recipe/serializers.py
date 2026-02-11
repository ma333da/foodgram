from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import (Cart, Favorite, Follow, Ingredient, IngredientAmount,
                     Recipe, Tag)

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class FollowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("author",)

    def validate(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Требуется аутентификация.")

        author = data.get("author")
        if user == author:
            raise (
                serializers.
                ValidationError("Нельзя подписаться на самого себя!")
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise (
                serializers.
                ValidationError("Вы уже подписаны на этого пользователя!"))
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        return Follow.objects.create(user=user, **validated_data)


class CropRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            "id", "email", "username", "first_name", "last_name",
            "is_subscribed", "recipes", "recipes_count"
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = None
        if request:
            limit = request.query_params.get("recipes_limit")
        qs = Recipe.objects.filter(author=obj.author).only(
            "id",
            "name",
            "image",
            "cooking_time"
        )
        if limit:
            try:
                qs = qs[:int(limit)]
            except (TypeError, ValueError):
                pass
        return CropRecipeSerializer(qs, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


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

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientAmount.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('__all__')


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=False)
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientamount_set',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        annotated = getattr(obj, 'is_favorited', None)
        if annotated is not None:
            return bool(annotated)

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        annotated = getattr(obj, 'is_in_shopping_cart', None)
        if annotated is not None:
            return bool(annotated)

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return Cart.objects.filter(user=user, recipe=obj).exists()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not instance.image:
            rep['image'] = 'Нету изображения'
        return rep

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        image = self.initial_data.get('image')

        if not image:
            raise serializers.ValidationError({
                'image': 'Нужна картинка.'
            })

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингредиент для рецепта.'
            })

        ingredient_counts = {}
        ingredient_ids = []

        for ingredient_item in ingredients:
            ingredient_id = ingredient_item.get('id')
            amount = ingredient_item.get('amount')

            if ingredient_id is None:
                raise serializers.ValidationError({
                    'ingredients': 'У ингредиента отсутствует id.'
                })

            try:
                ingredient_id_int = int(ingredient_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    'ingredients':
                        f'Некорректный id ингредиента: {ingredient_id}'
                })

            ingredient_ids.append(ingredient_id_int)

            if ingredient_id_int in ingredient_counts:
                ingredient_counts[ingredient_id_int] += 1
            else:
                ingredient_counts[ingredient_id_int] = 1

            try:
                if int(amount) <= 0:
                    raise serializers.ValidationError({
                        'ingredients':
                            'Кол-во ингредиентов должно быть больше 0.'
                    })
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    'ingredients': 'Кол-во ингредиента должен быть числом.'
                })
            existing_ids = set(
                Ingredient.objects.filter(id__in=ingredient_ids)
                .values_list('id', flat=True)
            )
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError({
                'ingredients': f'Ингредиенты не найдены: {sorted(missing_ids)}'
            })

        duplicates = [
            ingredient_id for ingredient_id,
            count in ingredient_counts.items() if count > 1
        ]

        if duplicates:
            duplicate_names = [
                Ingredient.objects.get(id=id).name for id in duplicates
            ]
            raise serializers.ValidationError({
                'ingredients': f'Ингредиенты должны быть уникальными. '
                               f'Повторяются: {", ".join(duplicate_names)}.'
            })

        data['ingredients'] = ingredients
        tags_ids = self.initial_data.get('tags')

        if not tags_ids:
            raise serializers.ValidationError({
                'tags': 'Нужен хоть один тег.'
            })

        try:
            tags_ids = [int(t) for t in tags_ids]
        except (TypeError, ValueError):
            raise serializers.ValidationError({
                'tags': 'Идентификаторы тегов должны быть числами.'
            })

        if len(tags_ids) != len(set(tags_ids)):
            raise serializers.ValidationError({
                'tags': 'Повторяющиеся теги не допускаются.'
            })

        existing_tags = set(
            Tag.objects.filter(id__in=tags_ids)
            .values_list('id', flat=True)
        )
        missing_tags = set(tags_ids) - existing_tags
        if missing_tags:
            raise serializers.ValidationError({
                'tags': f'Теги не найдены: {sorted(missing_tags)}'
            })

        data['tags_ids'] = tags_ids
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredient_amount_objects = [
            IngredientAmount(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
            for ingredient in ingredients
        ]
        IngredientAmount.objects.bulk_create(ingredient_amount_objects)

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_ids = validated_data.pop('tags_ids')
        recipe = Recipe.objects.create(image=image, **validated_data)
        tags_data = self.initial_data.get('tags')
        if tags_data:
            if len(tags_data) != len(set(tags_data)):
                raise serializers.ValidationError(
                    'Повторяющиеся теги не допускаются.'
                )
            recipe.tags.set(tags_data)
        if tags_ids:
            recipe.tags.set(tags_ids)
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
