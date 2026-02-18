from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FoodgramUserViewSet, IngredientsViewSet, RecipeViewSet,
                    TagViewSet)

app_name = 'api'

router = DefaultRouter()

router.register('ingredients', IngredientsViewSet)
router.register('recipe', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('users', FoodgramUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
