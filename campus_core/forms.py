from __future__ import annotations

import secrets
import string

from django import forms

from .models import AttendanceSession, Course, FoodOrder, MakeupClass, StudentProfile


class AttendanceSessionForm(forms.ModelForm):
    present_students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Unselected students are marked absent automatically.",
    )

    class Meta:
        model = AttendanceSession
        fields = ["course", "date", "time_slot"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.select_related("classroom")

        selected_course = self.data.get("course") or self.initial.get("course")
        if selected_course:
            try:
                course = Course.objects.get(pk=selected_course)
                self.fields["present_students"].queryset = StudentProfile.objects.filter(
                    enrollments__course=course
                ).select_related("user")
            except (Course.DoesNotExist, ValueError, TypeError):
                pass


class FoodOrderForm(forms.ModelForm):
    class Meta:
        model = FoodOrder
        fields = ["student", "item", "quantity", "break_slot"]


class CartCheckoutForm(forms.Form):
    student_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Enter student full name"}),
    )
    break_slot = forms.ChoiceField(choices=FoodOrder.BREAK_SLOTS)


class MakeupClassForm(forms.ModelForm):
    class Meta:
        model = MakeupClass
        fields = ["course", "faculty", "scheduled_for"]
        widgets = {
            "scheduled_for": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.remedial_code:
            instance.remedial_code = self.generate_remedial_code()
        if commit:
            instance.save()
        return instance

    @staticmethod
    def generate_remedial_code(length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))


class RemedialAttendanceForm(forms.Form):
    registration_no = forms.CharField(max_length=30)
    remedial_code = forms.CharField(max_length=12)


class StudentEnrollmentForm(forms.Form):
    student_name = forms.CharField(max_length=120)
    registration_no = forms.CharField(max_length=30)
    course = forms.ModelChoiceField(queryset=Course.objects.order_by("name"), required=False)
    face_image = forms.ImageField()


class AIAttendanceForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.order_by("name"))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    time_slot = forms.ChoiceField(choices=AttendanceSession.TIME_SLOTS)
    class_image = forms.ImageField(required=False, help_text="Upload class photo for AI face detection.")
