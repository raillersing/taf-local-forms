from django.contrib import admin

from .models import Student, Submission, TrainingModule, TrainingSession


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
    list_display = ("session_code", "module", "date", "location", "trainer_name", "is_active")
    list_filter = ("module", "is_active", "date")
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
