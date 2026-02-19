from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response

from .models import Recipe


def _generate_recipe_short_link(request, recipe_id):
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f"/recipe/{recipe_id}")

    return Response(status=status.HTTP_400_BAD_REQUEST)
