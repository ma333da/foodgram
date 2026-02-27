from django.urls import path

from . import views

app_name = 'recipe'

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        views._generate_recipe_short_link,
        name='short_link_view',
    ),
]
