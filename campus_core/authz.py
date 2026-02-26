from __future__ import annotations

from django.contrib.auth.models import User

from .models import StudentProfile

ROLE_FACULTY = "FACULTY"
ROLE_STUDENT = "STUDENT"
ROLE_VENDOR = "VENDOR"
ROLE_GUEST = "GUEST"


def get_user_role(user: User) -> str:
    if not user or not user.is_authenticated:
        return ROLE_GUEST

    if user.is_superuser or user.is_staff or user.groups.filter(name__iexact="faculty").exists():
        return ROLE_FACULTY

    if user.groups.filter(name__iexact="vendor").exists():
        return ROLE_VENDOR

    if user.groups.filter(name__iexact="student").exists():
        return ROLE_STUDENT

    if StudentProfile.objects.filter(user=user).exists():
        return ROLE_STUDENT

    if hasattr(user, "faculty_profile"):
        return ROLE_FACULTY

    return ROLE_FACULTY


def role_flags(user: User) -> dict[str, bool | str]:
    role = get_user_role(user)
    is_faculty = role == ROLE_FACULTY
    is_student = role == ROLE_STUDENT
    is_vendor = role == ROLE_VENDOR

    return {
        "user_role": role,
        "is_faculty": is_faculty,
        "is_student": is_student,
        "is_vendor": is_vendor,
        "can_attendance": is_faculty,
        "can_food": is_faculty or is_student or is_vendor,
        "can_analytics": is_faculty or is_vendor,
        "can_resources": is_faculty,
        "can_makeup": is_faculty or is_student,
        "can_remedial": is_faculty or is_student,
        "can_alerts": is_faculty or is_vendor,
        "can_ai": is_faculty,
    }
