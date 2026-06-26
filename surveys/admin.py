from django.contrib import admin
from django.conf import settings

from .models import FormPresence, LearningResource, Module3Submission, Module4Submission, Module5Submission, Module6Submission, Module7Submission, Module8Submission, Student, Submission, TrainingModule, TrainingSession

admin.site.site_header = getattr(settings, "ADMIN_SITE_HEADER", "TAf Local Forms")
admin.site.site_title = getattr(settings, "ADMIN_SITE_TITLE", "TAf Admin")
admin.site.index_title = getattr(settings, "ADMIN_INDEX_TITLE", "Administration formateur")
admin.site.site_url = "/dashboard/"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("school_id_number", "full_name", "class_level", "group_name")
    list_filter = ("class_level", "group_name")
    search_fields = ("school_id_number", "full_name")


@admin.register(TrainingModule)
class TrainingModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("session_code", "module", "date", "location", "trainer_name", "is_active", "accepting_responses")
    list_filter = ("module", "is_active", "accepting_responses", "date")
    search_fields = ("session_code", "location", "trainer_name")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "school_id_number_snapshot",
        "student",
        "session",
        "computed_score",
        "created_at",
    )
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(Module3Submission)
class Module3SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "school_id_number_snapshot",
        "student",
        "session",
        "computed_score",
        "created_at",
    )
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(Module4Submission)
class Module4SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "school_id_number_snapshot",
        "student",
        "session",
        "computed_score",
        "created_at",
    )
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(Module5Submission)
class Module5SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "school_id_number_snapshot",
        "student",
        "session",
        "computed_score",
        "created_at",
    )
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(Module6Submission)
class Module6SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "school_id_number_snapshot",
        "student",
        "session",
        "computed_score",
        "created_at",
    )
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(Module7Submission)
class Module7SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "school_id_number_snapshot",
        "student",
        "session",
        "computed_score",
        "created_at",
    )
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(Module8Submission)
class Module8SubmissionAdmin(admin.ModelAdmin):
    list_display = ("school_id_number_snapshot", "student", "session", "computed_score", "created_at")
    list_filter = ("session", "student__class_level", "student__group_name", "created_at")
    search_fields = ("school_id_number_snapshot", "student__school_id_number", "student__full_name")
    autocomplete_fields = ("student", "session")
    readonly_fields = ("computed_score",)


@admin.register(FormPresence)
class FormPresenceAdmin(admin.ModelAdmin):
    list_display = ("client_id", "module_code", "training_session", "status", "last_seen_at")
    list_filter = ("module_code", "status", "training_session")
    search_fields = ("client_id", "module_code")
    readonly_fields = ("started_at", "last_seen_at")


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "resource_type", "module_number", "is_published", "updated_at")
    list_filter = ("is_published", "resource_type", "module_number")
    search_fields = ("title", "description", "source")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
