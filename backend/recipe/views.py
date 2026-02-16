

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..api.serializers import RecipeSerializer
from .models import Recipe


class RecipeShortLinkViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (AllowAny,)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = self._generate_recipe_short_link(request, recipe)
        return Response({"short-link": short_link})

    def _generate_recipe_short_link(self, request, recipe):
        return request.build_absolute_uri(f"/s/{recipe.id}")
