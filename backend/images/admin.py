from django.contrib import admin
from .models import ImageData, IdolInfo, ImageTag


@admin.register(ImageData)
class ImageDataAdmin(admin.ModelAdmin):
    list_display = ['hashed', 'source_url', 'created_at']
    list_filter = ['created_at']
    search_fields = ['source_url']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(IdolInfo)
class IdolInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'group_name', 'idol_name', 'created_at']
    list_filter = ['group_name', 'created_at']
    search_fields = ['group_name', 'idol_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ImageTag)
class ImageTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'tag_name', 'created_at']
    list_filter = ['tag_name', 'created_at']
    search_fields = ['tag_name']
    readonly_fields = ['created_at']
