"""Reliable, session-aware metrics for trainer dashboards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db.models import QuerySet, Sum

from .constants import MODULE_METADATA
from .models import (
    Module1Submission,
    Module3Submission,
    Module4Submission,
    Module5Submission,
    Module6Submission,
    Module7Submission,
    Module8Submission,
    Student,
    Submission,
    TrainingSession,
)


SUBMISSION_MODELS = {
    "MODULE_1": Module1Submission,
    "MODULE_2": Submission,
    "MODULE_3": Module3Submission,
    "MODULE_4": Module4Submission,
    "MODULE_5": Module5Submission,
    "MODULE_6": Module6Submission,
    "MODULE_7": Module7Submission,
    "MODULE_8": Module8Submission,
}


def normalize_student_name(value: str) -> str:
    """Normalize spacing and case while preserving letters and accents."""

    return " ".join((value or "").split()).casefold()


def normalize_student_identity(full_name: str, class_level: str) -> tuple[str, str]:
    return normalize_student_name(full_name), (class_level or "").strip().casefold()


def find_student_by_identity(full_name: str, class_level: str) -> Student | None:
    """Find an existing student using the approved name + class identity."""

    expected = normalize_student_identity(full_name, class_level)
    candidates = Student.objects.filter(class_level__iexact=(class_level or "").strip())
    return next(
        (student for student in candidates if normalize_student_identity(student.full_name, student.class_level) == expected),
        None,
    )


def canonical_student_name(full_name: str) -> str:
    return " ".join((full_name or "").split())


def submission_queryset(module_code: str, session: TrainingSession | None = None) -> QuerySet:
    model = SUBMISSION_MODELS[module_code]
    queryset = model.objects.filter(session__module__code=module_code)
    if session is not None:
        queryset = queryset.filter(session=session)
    return queryset


def active_session_for_module(module_code: str) -> TrainingSession | None:
    return (
        TrainingSession.objects.filter(module__code=module_code, is_active=True)
        .select_related("module")
        .order_by("-date", "session_code")
        .first()
    )


def unique_student_identities(querysets: Iterable[QuerySet]) -> set[tuple[str, str]]:
    identities: set[tuple[str, str]] = set()
    for queryset in querysets:
        for full_name, class_level in queryset.values_list(
            "student__full_name", "student__class_level"
        ):
            identities.add(normalize_student_identity(full_name, class_level))
    return identities


def submission_count(querysets: Iterable[QuerySet]) -> int:
    return sum(queryset.count() for queryset in querysets)


def module_score_metrics(module_code: str, queryset: QuerySet) -> tuple[int, int, float | None]:
    """Return score sum, possible score and percentage; Module 1 is not scored."""

    if module_code == "MODULE_1":
        return 0, 0, None
    max_score = MODULE_METADATA.get(module_code, {}).get("max_score", 0)
    total = queryset.aggregate(total=Sum("computed_score"))["total"] or 0
    possible = queryset.count() * max_score
    percentage = round((total / possible) * 100, 1) if possible else None
    return total, possible, percentage


@dataclass(frozen=True)
class DashboardTotals:
    submissions: int
    unique_students: int


def dashboard_totals(*, active_only: bool) -> DashboardTotals:
    querysets = []
    for module_code, model in SUBMISSION_MODELS.items():
        queryset = model.objects.filter(session__module__code=module_code)
        if active_only:
            queryset = queryset.filter(session__is_active=True)
        querysets.append(queryset)
    return DashboardTotals(
        submissions=submission_count(querysets),
        unique_students=len(unique_student_identities(querysets)),
    )


def sessions_with_responses_count() -> int:
    session_ids: set[int] = set()
    for module_code, model in SUBMISSION_MODELS.items():
        session_ids.update(
            model.objects.filter(session__module__code=module_code).values_list("session_id", flat=True)
        )
    return len(session_ids)
