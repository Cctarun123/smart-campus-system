from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Block(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Classroom(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="classrooms")
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=40)

    class Meta:
        unique_together = ("block", "name")

    def __str__(self) -> str:
        return f"{self.block.name} - {self.name}"


class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="faculty_profile")
    department = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    registration_no = models.CharField(max_length=30, unique=True)
    parent_contact = models.CharField(max_length=40, blank=True)

    def __str__(self) -> str:
        return f"{self.registration_no} - {self.user.get_full_name() or self.user.username}"


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    faculty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="courses")
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")

    class Meta:
        unique_together = ("student", "course")

    def __str__(self) -> str:
        return f"{self.student.registration_no} -> {self.course.code}"


class AttendanceSession(models.Model):
    TIME_SLOTS = [
        ("MORNING", "Morning"),
        ("AFTERNOON", "Afternoon"),
        ("EVENING", "Evening"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance_sessions")
    date = models.DateField(default=timezone.localdate)
    time_slot = models.CharField(max_length=20, choices=TIME_SLOTS, default="MORNING")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_attendance_sessions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "date", "time_slot")

    def __str__(self) -> str:
        return f"{self.course.code} | {self.date} | {self.time_slot}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by_remedial_code = models.BooleanField(default=False)

    class Meta:
        unique_together = ("session", "student")


class NotificationLog(models.Model):
    CHANNEL_CHOICES = [
        ("STUDENT", "Student"),
        ("PARENT", "Parent"),
    ]

    recipient = models.CharField(max_length=120)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.channel}: {self.recipient}"


class FoodStall(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class FoodItem(models.Model):
    stall = models.ForeignKey(FoodStall, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image_url = models.URLField(blank=True)

    class Meta:
        unique_together = ("stall", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.stall.name})"


class FoodOrder(models.Model):
    BREAK_SLOTS = [
        ("SHORT", "Short Break"),
        ("LUNCH", "Lunch"),
        ("EVENING", "Evening Break"),
    ]

    STATUS_CHOICES = [
        ("PLACED", "Placed"),
        ("READY", "Ready"),
        ("COLLECTED", "Collected"),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="food_orders")
    item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    break_slot = models.CharField(max_length=20, choices=BREAK_SLOTS, default="LUNCH")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PLACED")
    ordered_at = models.DateTimeField(auto_now_add=True)


class StudentFaceProfile(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name="face_profile")
    face_image = models.ImageField(upload_to="student_faces/")
    face_encoding = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"FaceProfile({self.student.registration_no})"


class PaymentHistory(models.Model):
    student_name = models.CharField(max_length=120)
    break_slot = models.CharField(max_length=20, choices=FoodOrder.BREAK_SLOTS, default="LUNCH")
    payment_method = models.CharField(max_length=50)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    items = models.JSONField(default=list)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.student_name} | {self.payment_method} | {self.paid_at:%Y-%m-%d %H:%M}"


class MakeupClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="makeup_classes")
    faculty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="makeup_classes")
    scheduled_for = models.DateTimeField()
    remedial_code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.course.code} ({self.remedial_code})"


class MakeupAttendance(models.Model):
    makeup_class = models.ForeignKey(MakeupClass, on_delete=models.CASCADE, related_name="attendance_entries")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="makeup_attendance_entries")
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("makeup_class", "student")
