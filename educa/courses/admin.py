from django.contrib import admin
from django.utils.html import format_html
from .models import Subject, Course, Module, Content, Text, Video, Image, File


# Subject Admin
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["title", "slug"]
    prepopulated_fields = {"slug": ("title",)}


# Module Inline for Course Admin
class ModuleInline(admin.StackedInline):
    model = Module
    extra = 0  # No extra empty inline forms


# Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "owner", "created"]
    list_filter = ["created", "subject"]
    search_fields = ["title", "overview", "owner__username"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ModuleInline]


# Content Inline for Module Admin
class ContentInline(admin.TabularInline):
    model = Content
    extra = 0  # No extra empty inline forms
    fields = ("content_type", "object_id", "owner", "order", "view_content_link")
    readonly_fields = ("content_type", "view_content_link")  # Read-only link

    def view_content_link(self, obj):
        # Create a link to the Content object in the admin
        if obj.id:
            return format_html(
                '<a href="/admin/courses/content/{}/change/">View Content</a>', obj.id
            )
        return "N/A"

    view_content_link.short_description = "View Content"


# Module Admin
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order", "view_course_link"]
    list_filter = ["course"]
    search_fields = ["title", "course__title"]
    inlines = [ContentInline]

    def view_course_link(self, obj):
        # Create a link to the related Course in the admin
        if obj.course.id:
            return format_html(
                '<a href="/admin/courses/course/{}/change/">View Course</a>',
                obj.course.id,
            )
        return "N/A"

    view_course_link.short_description = "View Course"


# Register Individual Content Types
@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created", "updated", "view_module_link"]
    search_fields = ["title", "content", "owner__username"]

    def view_module_link(self, obj):
        content = Content.objects.filter(
            object_id=obj.id, content_type__model=obj._meta.model_name
        ).first()
        if content and content.module:
            return format_html(
                '<a href="/admin/courses/module/{}/change/">View Module</a>',
                content.module.id,
            )
        return "N/A"

    view_module_link.short_description = "View Module"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created", "updated", "view_module_link"]
    search_fields = ["title", "url", "owner__username"]

    def view_module_link(self, obj):
        content = Content.objects.filter(
            object_id=obj.id, content_type__model=obj._meta.model_name
        ).first()
        if content and content.module:
            return format_html(
                '<a href="/admin/courses/module/{}/change/">View Module</a>',
                content.module.id,
            )
        return "N/A"

    view_module_link.short_description = "View Module"


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created", "updated", "view_module_link"]
    search_fields = ["title", "file", "owner__username"]

    def view_module_link(self, obj):
        content = Content.objects.filter(
            object_id=obj.id, content_type__model=obj._meta.model_name
        ).first()
        if content and content.module:
            return format_html(
                '<a href="/admin/courses/module/{}/change/">View Module</a>',
                content.module.id,
            )
        return "N/A"

    view_module_link.short_description = "View Module"


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created", "updated", "view_module_link"]
    search_fields = ["title", "file", "owner__username"]

    def view_module_link(self, obj):
        content = Content.objects.filter(
            object_id=obj.id, content_type__model=obj._meta.model_name
        ).first()
        if content and content.module:
            return format_html(
                '<a href="/admin/courses/module/{}/change/">View Module</a>',
                content.module.id,
            )
        return "N/A"

    view_module_link.short_description = "View Module"


# Content Admin
@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = [
        "module",
        "owner",
        "content_type",
        "order",
        "object_id",
        "view_module_link",
    ]
    list_filter = ["module__course", "content_type", "owner"]
    search_fields = ["module__title", "owner__username", "content_type__model"]

    def view_module_link(self, obj):
        content = Content.objects.filter(
            object_id=obj.id, content_type__model=obj._meta.model_name
        ).first()
        if content and content.module:
            return format_html(
                '<a href="/admin/courses/module/{}/change/">View Module</a>',
                content.module.id,
            )
        return "N/A"

    view_module_link.short_description = "View Module"
