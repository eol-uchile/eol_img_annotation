from django.contrib import admin
from .models import ImgAnnotationModel

# Register your models here.


class ImgAnnotationAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('user', 'annotation_id', 'course_key', 'usage_key')
    search_fields = ['user__username', 'annotation_id', 'course_key', 'usage_key']

admin.site.register(ImgAnnotationModel, ImgAnnotationAdmin)

