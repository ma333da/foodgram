from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import (
    IngredientsViewSet,
    RecipeViewSet,
    TagViewSet,
    CustomUserViewSet
)

router = DefaultRouter()
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('users', CustomUserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
