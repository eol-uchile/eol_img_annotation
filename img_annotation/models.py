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
    ROLE_CHOICES = (("staff", "staff"), ("student", "student"))
    annotation_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.TextField(choices=ROLE_CHOICES)
    body = models.TextField(blank=True, default="")
    course_key = CourseKeyField(max_length=255, default=None)
    usage_key = UsageKeyField(max_length=255, default=None)
    target = models.CharField(max_length=250, default="")
