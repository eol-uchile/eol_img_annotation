from django.contrib.auth.models import User
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField

# Create your models here.

class ImgAnnotationModel(models.Model):
    """
        .
    """
    class Meta:
        index_together = [
            ["annotation_id", "user", "course_key", "usage_key"],
        ]
        unique_together = [
            ["annotation_id", "user", "course_key", "usage_key"],
        ]
        app_label  = 'img_annotation'
    
    ROLE_CHOICES = (("staff", "staff"), ("student", "student"))
    annotation_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.TextField(choices=ROLE_CHOICES)
    body = models.TextField(blank=True, default="")
    course_key = CourseKeyField(max_length=255, default=None)
    usage_key = UsageKeyField(max_length=255, default=None)
    target = models.TextField(blank=True, default="")

class OverlayModel(models.Model):
    """
    Stores information related to overlays linked to an img_annotation_block.
    """
    class Meta:
        index_together = [
            ["course_key", "usage_key"],
        ]
        app_label  = 'img_annotation'
    
    OVERLAY_CHOICES = (("highlighted_overlay", "rectangle_overlay"), ("fixed_size_overlay", "arrow_overlay"))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.TextField(choices=OVERLAY_CHOICES)
    course_key = CourseKeyField(max_length=255, default=None)
    usage_key = UsageKeyField(max_length=255, default=None)
    height = models.DecimalField(max_digits=32, decimal_places=30, null=True, blank=True)
    width = models.DecimalField(max_digits=32, decimal_places=30, null=True, blank=True)
    position_x = models.DecimalField(max_digits=32, decimal_places=30)
    position_y = models.DecimalField(max_digits=32, decimal_places=30)
