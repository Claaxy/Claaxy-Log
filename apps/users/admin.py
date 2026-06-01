from django.contrib import admin

from apps.users.models import AllowedUser


@admin.register(AllowedUser)
class AllowedUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'google_email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'google_email')
