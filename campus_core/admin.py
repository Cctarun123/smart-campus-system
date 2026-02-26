from django.contrib import admin

from .models import (
    AttendanceRecord,
    AttendanceSession,
    Block,
    Classroom,
    Course,
    Enrollment,
    FacultyProfile,
    FoodItem,
    FoodOrder,
    PaymentHistory,
    StudentFaceProfile,
    FoodStall,
    MakeupAttendance,
    MakeupClass,
    NotificationLog,
    StudentProfile,
)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "block", "capacity")
    list_filter = ("block",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("registration_no", "user", "parent_contact")
    search_fields = ("registration_no", "user__username", "user__first_name", "user__last_name")


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "faculty", "classroom")
    search_fields = ("code", "name")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course")
    list_filter = ("course",)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("course", "date", "time_slot", "created_by", "created_at")
    list_filter = ("time_slot", "date")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "status", "marked_by_remedial_code")
    list_filter = ("status",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "channel", "created_at")
    list_filter = ("channel",)


@admin.register(FoodStall)
class FoodStallAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "stall", "price", "image_url")
    search_fields = ("name", "stall__name")


@admin.register(FoodOrder)
class FoodOrderAdmin(admin.ModelAdmin):
    list_display = ("student", "item", "quantity", "break_slot", "status", "ordered_at")
    list_filter = ("break_slot", "status")


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ("student_name", "payment_method", "break_slot", "total", "paid_at")
    list_filter = ("payment_method", "break_slot")
    search_fields = ("student_name",)


@admin.register(StudentFaceProfile)
class StudentFaceProfileAdmin(admin.ModelAdmin):
    list_display = ("student", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("student__registration_no", "student__user__username")


@admin.register(MakeupClass)
class MakeupClassAdmin(admin.ModelAdmin):
    list_display = ("course", "faculty", "scheduled_for", "remedial_code")


@admin.register(MakeupAttendance)
class MakeupAttendanceAdmin(admin.ModelAdmin):
    list_display = ("makeup_class", "student", "marked_at")
