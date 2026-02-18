from django.shortcuts import redirect
from rest_framework.generics import get_object_or_404

from .models import Recipe


def _generate_recipe_short_link(request, recipe_id):
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f"/api/recipe/{recipe_id}")
