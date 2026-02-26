from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from .models import Recipe


def _generate_recipe_short_link(request, recipe_id):
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}')

    raise ValidationError(f'Рецепта с id {recipe_id} не существует!')
