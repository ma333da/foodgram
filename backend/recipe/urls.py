from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FoodgramUserViewSet, IngredientsViewSet, RecipeViewSet,
                    TagViewSet)

router = DefaultRouter()
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('users', FoodgramUserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
