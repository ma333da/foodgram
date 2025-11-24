from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BaseUser

from users.models import Follow


@admin.register(BaseUser)
class BaseUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
    )
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Follow)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
