from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeShortLinkViewSet

router = DefaultRouter()

router.register(r'recipes', RecipeShortLinkViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
