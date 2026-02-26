from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("attendance/mark/", views.attendance_mark, name="attendance-mark"),
    path("attendance/timesheet/", views.attendance_timesheet, name="attendance-timesheet"),
    path("attendance/ai-mark/", views.attendance_ai_mark, name="attendance-ai-mark"),
    path("attendance/enroll/", views.student_course_enroll, name="student-course-enroll"),
    path("attendance/report/<int:session_id>/", views.attendance_report, name="attendance-report"),
    path("food/order/", views.food_order, name="food-order"),
    path("food/bills/", views.bills_dashboard, name="bills-dashboard"),
    path("food/history/", views.order_history, name="order-history"),
    path("food/analytics/", views.food_analytics, name="food-analytics"),
    path("resources/", views.resource_dashboard, name="resource-dashboard"),
    path("makeup/schedule/", views.makeup_schedule, name="makeup-schedule"),
    path("makeup/<int:makeup_id>/", views.makeup_detail, name="makeup-detail"),
    path("makeup/<int:makeup_id>/check/", views.makeup_presence_check, name="makeup-presence-check"),
    path("makeup/remedial-attendance/", views.remedial_attendance, name="remedial-attendance"),
    path("notifications/", views.notifications_log, name="notifications-log"),
    path("ai-preview/", views.ai_stub, name="ai-preview"),
]
