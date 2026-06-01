from django.contrib import admin

from apps.projects.models import Project, VoiceNote


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'customer_name', 'user', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('project_name', 'customer_name')


@admin.register(VoiceNote)
class VoiceNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'processing_status', 'created_at')
    list_filter = ('processing_status',)
