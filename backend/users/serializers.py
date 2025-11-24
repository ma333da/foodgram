from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.models import Follow
from recipe.models import Recipe
from drf_extra_fields.fields import Base64ImageField
from foodgram.constants import MAX_USERNAME_LENGTH

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True
    )
    username = serializers.CharField(
        max_length=MAX_USERNAME_LENGTH,
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'password',
            'username',
            'first_name',
            'last_name'
        )


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
