from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls'),),
    path('s/<int:recipe_id>/', include('recipe.urls', namespace='recipe')),
]
