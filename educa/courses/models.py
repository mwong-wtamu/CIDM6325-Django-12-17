from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.core.validators import FileExtensionValidator
from .fields import OrderField
from django.core.exceptions import ValidationError
import os


class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Course(models.Model):
    owner = models.ForeignKey(
        User, related_name="courses_created", on_delete=models.CASCADE
    )
    subject = models.ForeignKey(
        Subject, related_name="courses", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, related_name="courses_joined", blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name="modules", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=["course"])

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Content(models.Model):
    module = models.ForeignKey(
        Module, related_name="contents", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        User, related_name="owned_contents", on_delete=models.CASCADE
    )  # Add ownership
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={"model__in": ("text", "video", "image", "file")},
    )
    order = OrderField(blank=True, for_fields=["module"])

    class Meta:
        ordering = ["order"]

    object_id = models.PositiveIntegerField()
    item = GenericForeignKey("content_type", "object_id")


class ItemBase(models.Model):
    owner = models.ForeignKey(
        User, related_name="%(class)s_related", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def render(self):
        return render_to_string(
            f"courses/content/{self._meta.model_name}.html", {"item": self}
        )

    def __str__(self):
        return self.title


class Text(ItemBase):
    content = models.TextField()

    file = models.FileField(
        upload_to="texts",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["txt"])],
    )

    def clean(self):
        """
        Ensure either 'content' or 'file' is provided, but not both.
        """
        if not self.content and not self.file:
            raise ValidationError(
                "You must provide either text content or upload a text file."
            )
        if self.content and self.file:
            raise ValidationError(
                "You cannot provide both text content and a text file."
            )

    def render(self):
        """
        Render video content using a dedicated template.
        """
        return render_to_string("courses/content/text.html", {"item": self})


class File(ItemBase):
    file = models.FileField(
        upload_to="files",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    def render(self):
        """
        Render content using a dedicated template.
        """
        return render_to_string("courses/content/file.html", {"item": self})


class Image(ItemBase):
    file = models.FileField(
        upload_to="images",
        validators=[FileExtensionValidator(allowed_extensions=["png"])],
    )


class Video(ItemBase):
    url = models.URLField(blank=True, null=True)  # For YouTube links
    file = models.FileField(
        upload_to="videos",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["mp4"])],
    )

    def clean(self):
        """
        Custom validation to ensure that either a YouTube URL or an MP4 file is provided.
        """
        if not self.url and not self.file:
            raise ValidationError(
                "You must provide either a YouTube URL or an MP4 file."
            )
        if self.url and not self.url.startswith(
            ("http://www.youtube.com", "https://www.youtube.com")
        ):
            raise ValidationError("Only YouTube links are allowed in the URL field.")
        if self.file and not self.file.name.lower().endswith(".mp4"):
            raise ValidationError("Only MP4 files are allowed for video uploads.")

    def save(self, *args, **kwargs):
        self.clean()  # Call the clean method for validation
        super().save(*args, **kwargs)

    def render(self):
        """
        Render video content using a dedicated template.
        """
        return render_to_string("courses/content/video.html", {"item": self})
