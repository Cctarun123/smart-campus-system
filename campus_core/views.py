from __future__ import annotations

from collections import Counter
from datetime import timedelta
from decimal import Decimal
from functools import wraps
import re

import cv2
import face_recognition
import numpy as np
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .authz import ROLE_FACULTY, ROLE_STUDENT, ROLE_VENDOR, get_user_role
from .forms import (
    AIAttendanceForm,
    AttendanceSessionForm,
    CartCheckoutForm,
    MakeupClassForm,
    RemedialAttendanceForm,
    StudentEnrollmentForm,
)
from .models import (
    AttendanceRecord,
    AttendanceSession,
    Block,
    Classroom,
    Course,
    Enrollment,
    FoodItem,
    FoodStall,
    FoodOrder,
    PaymentHistory,
    StudentFaceProfile,
    MakeupAttendance,
    MakeupClass,
    NotificationLog,
    StudentProfile,
)

CART_SESSION_KEY = "food_cart"
COUPON_SESSION_KEY = "food_coupon"
CHECKOUT_SESSION_KEY = "food_checkout_details"
COUPON_RATES = {
    "SAVE10": Decimal("0.10"),
    "LPU20": Decimal("0.20"),
}


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required(login_url="login")
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role not in allowed_roles:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("home")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def _get_cart(request) -> dict[str, int]:
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart: dict[str, int]) -> None:
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _guess_category(item_name: str) -> str:
    lower_name = item_name.lower()
    if "pizza" in lower_name:
        return "Pizza"
    if "burger" in lower_name:
        return "Burger"
    if any(word in lower_name for word in ["juice", "coffee", "tea", "shake", "drink", "beverage"]):
        return "Beverage"
    if any(word in lower_name for word in ["chicken", "wings", "bucket"]):
        return "Chicken"
    if any(word in lower_name for word in ["fish", "prawn", "shrimp", "seafood"]):
        return "Seafood"
    if any(word in lower_name for word in ["cake", "bread", "bakery", "croissant", "pastry"]):
        return "Bakery"
    return "Bakery"


def _cart_rows(cart: dict[str, int]):
    item_ids = [int(item_id) for item_id in cart.keys() if str(item_id).isdigit()]
    items = {item.id: item for item in FoodItem.objects.select_related("stall").filter(id__in=item_ids)}
    rows = []
    subtotal = Decimal("0.00")
    cleaned_cart = {}

    for item_id_str, qty in cart.items():
        if not item_id_str.isdigit():
            continue
        item = items.get(int(item_id_str))
        if not item:
            continue

        quantity = max(1, int(qty))
        cleaned_cart[item_id_str] = quantity

        line_total = item.price * quantity
        subtotal += line_total

        rows.append(
            {
                "item": item,
                "qty": quantity,
                "line_total": line_total,
                "item_id": item.id,
            }
        )

    rows.sort(key=lambda row: row["item"].name)
    return rows, subtotal, cleaned_cart


def _get_or_create_student_by_name(name: str) -> StudentProfile:
    cleaned_name = " ".join(name.split()).strip()
    existing = StudentProfile.objects.select_related("user").filter(
        user__first_name__iexact=cleaned_name
    ).first()
    if existing:
        return existing

    base = re.sub(r"[^a-z0-9]+", "", cleaned_name.lower())[:16] or "student"
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}{suffix}"

    user = User.objects.create(username=username, first_name=cleaned_name)

    reg_seed = re.sub(r"[^A-Z0-9]+", "", cleaned_name.upper())[:6] or "STD"
    registration_no = f"GUEST-{reg_seed}"
    reg_suffix = 1
    while StudentProfile.objects.filter(registration_no=registration_no).exists():
        reg_suffix += 1
        registration_no = f"GUEST-{reg_seed}{reg_suffix}"

    return StudentProfile.objects.create(user=user, registration_no=registration_no)


def _file_to_rgb_image(uploaded_file):
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    np_arr = np.frombuffer(raw, dtype=np.uint8)
    bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _extract_single_face_encoding(uploaded_file):
    rgb = _file_to_rgb_image(uploaded_file)
    if rgb is None:
        return None
    encodings = face_recognition.face_encodings(rgb)
    if not encodings:
        return None
    return encodings[0].tolist()


def _extract_multiple_face_encodings(uploaded_file):
    rgb = _file_to_rgb_image(uploaded_file)
    if rgb is None:
        return []
    return [enc.tolist() for enc in face_recognition.face_encodings(rgb)]


@login_required(login_url="login")
def home(request):
    return render(request, "campus_core/home.html")


@role_required(ROLE_FACULTY)
def attendance_mark(request):
    initial = {}
    if request.method != "POST":
        selected_course = request.GET.get("course", "").strip()
        if selected_course.isdigit():
            initial["course"] = int(selected_course)
        else:
            default_course = Course.objects.order_by("name").first()
            if default_course:
                initial["course"] = default_course.id
    form = AttendanceSessionForm(request.POST or None, initial=initial)
    students = list(form.fields["present_students"].queryset)
    selected_present_ids = set()
    if request.method == "POST":
        selected_present_ids = set(request.POST.getlist("present_students"))
    else:
        selected_present_ids = {
            str(student.id)
            for student in students
            if hasattr(student, "face_profile") and student.face_profile.is_active
        }

    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.created_by = request.user if request.user.is_authenticated else None
        session.save()

        enrolled_students = StudentProfile.objects.filter(
            enrollments__course=session.course
        ).distinct()
        present_students = form.cleaned_data["present_students"]

        records = []
        absentee_notifications = []
        for student in enrolled_students:
            is_present = student in present_students
            status = "PRESENT" if is_present else "ABSENT"
            records.append(
                AttendanceRecord(session=session, student=student, status=status)
            )
            if not is_present:
                msg = f"Absent in {session.course.code} on {session.date} ({session.time_slot})"
                absentee_notifications.append(
                    NotificationLog(recipient=student.user.username, message=msg, channel="STUDENT")
                )
                if student.parent_contact:
                    absentee_notifications.append(
                        NotificationLog(
                            recipient=student.parent_contact,
                            message=f"Ward {student.registration_no} {msg}",
                            channel="PARENT",
                        )
                    )

        AttendanceRecord.objects.bulk_create(records)
        NotificationLog.objects.bulk_create(absentee_notifications)

        messages.success(
            request,
            f"Attendance captured instantly. {len(absentee_notifications)} absentee notifications simulated.",
        )
        return redirect("attendance-report", session_id=session.id)

    return render(
        request,
        "campus_core/attendance_mark.html",
        {
            "form": form,
            "students": students,
            "selected_present_ids": selected_present_ids,
        },
    )


@role_required(ROLE_FACULTY)
def attendance_report(request, session_id: int):
    session = get_object_or_404(AttendanceSession.objects.select_related("course"), id=session_id)
    records = session.records.select_related("student__user")
    absent = records.filter(status="ABSENT")
    return render(
        request,
        "campus_core/attendance_report.html",
        {
            "session": session,
            "records": records,
            "absent_count": absent.count(),
        },
    )


@role_required(ROLE_FACULTY)
def attendance_timesheet(request):
    start_str = request.GET.get("start", "").strip()
    if start_str:
        try:
            start_date = timezone.datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
    else:
        today = timezone.localdate()
        start_date = today - timedelta(days=today.weekday())

    week_days = [start_date + timedelta(days=i) for i in range(7)]
    end_date = week_days[-1]

    records = (
        AttendanceRecord.objects.filter(session__date__gte=start_date, session__date__lte=end_date)
        .select_related("student__user", "session")
        .order_by("student__registration_no", "session__date")
    )

    row_map = {}
    for rec in records:
        key = rec.student_id
        if key not in row_map:
            row_map[key] = {
                "student": rec.student,
                "hours_by_day": {day: 0 for day in week_days},
                "present_count": 0,
            }
        if rec.status == "PRESENT":
            row_map[key]["hours_by_day"][rec.session.date] += 1
            row_map[key]["present_count"] += 1

    rows = []
    for _, data in row_map.items():
        total_hours = sum(data["hours_by_day"].values())
        day_hours = [data["hours_by_day"][day] for day in week_days]
        rows.append(
            {
                "student": data["student"],
                "hours_by_day": data["hours_by_day"],
                "day_hours": day_hours,
                "total_hours": total_hours,
                "present_count": data["present_count"],
            }
        )
    rows.sort(key=lambda r: r["student"].registration_no)

    return render(
        request,
        "campus_core/attendance_timesheet.html",
        {
            "week_days": week_days,
            "rows": rows,
            "start_date": start_date,
            "end_date": end_date,
            "prev_start": start_date - timedelta(days=7),
            "next_start": start_date + timedelta(days=7),
        },
    )


@role_required(ROLE_FACULTY)
def attendance_ai_mark(request):
    initial = {}
    selected_course_id = request.GET.get("course", "").strip() if request.method == "GET" else ""
    if selected_course_id.isdigit():
        initial["course"] = int(selected_course_id)
    else:
        default_course = Course.objects.order_by("name").first()
        if default_course:
            initial["course"] = default_course.id
    initial["date"] = timezone.localdate()
    form = AIAttendanceForm(request.POST or None, request.FILES or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        course = form.cleaned_data["course"]
        date = form.cleaned_data["date"]
        time_slot = form.cleaned_data["time_slot"]
        class_image = form.cleaned_data["class_image"]
        selected_student_id = request.POST.get("selected_student_id", "").strip()

        matched_student_ids = set()

        enrolled_students = list(
            StudentProfile.objects.filter(
                enrollments__course=course,
                face_profile__is_active=True,
            )
            .select_related("user", "face_profile")
            .distinct()
        )
        if not enrolled_students:
            messages.error(request, "No face-enrolled students found for this course.")
            return render(
                request,
                "campus_core/attendance_ai_mark.html",
                {"form": form, "enrolled_face_students": [], "selected_course_id": str(course.id)},
            )

        if selected_student_id.isdigit():
            selected_id = int(selected_student_id)
            if any(student.id == selected_id for student in enrolled_students):
                matched_student_ids.add(selected_id)
            else:
                messages.error(request, "Selected student is not face-enrolled in this course.")
                return render(
                    request,
                    "campus_core/attendance_ai_mark.html",
                    {
                        "form": form,
                        "enrolled_face_students": enrolled_students,
                        "selected_course_id": str(course.id),
                    },
                )
            detected_faces_count = 1
        else:
            if not class_image:
                matched_student_ids = {student.id for student in enrolled_students}
                detected_faces_count = len(matched_student_ids)
            else:
                detected_encodings = _extract_multiple_face_encodings(class_image)
                if not detected_encodings:
                    messages.error(request, "No faces detected in class image.")
                    return render(
                        request,
                        "campus_core/attendance_ai_mark.html",
                        {
                            "form": form,
                            "enrolled_face_students": enrolled_students,
                            "selected_course_id": str(course.id),
                        },
                    )

                known_encodings = [np.array(student.face_profile.face_encoding, dtype=np.float64) for student in enrolled_students]
                threshold = 0.45
                for detected in detected_encodings:
                    detected_np = np.array(detected, dtype=np.float64)
                    distances = face_recognition.face_distance(known_encodings, detected_np)
                    if len(distances) == 0:
                        continue
                    best_idx = int(np.argmin(distances))
                    if float(distances[best_idx]) <= threshold:
                        matched_student_ids.add(enrolled_students[best_idx].id)
                detected_faces_count = len(detected_encodings)

        session, _ = AttendanceSession.objects.get_or_create(
            course=course,
            date=date,
            time_slot=time_slot,
            defaults={"created_by": request.user if request.user.is_authenticated else None},
        )
        session.records.all().delete()

        records = []
        absentee_notifications = []
        for student in StudentProfile.objects.filter(enrollments__course=course).distinct():
            status = "PRESENT" if student.id in matched_student_ids else "ABSENT"
            records.append(AttendanceRecord(session=session, student=student, status=status))
            if status == "ABSENT":
                msg = f"Absent in {session.course.code} on {session.date} ({session.time_slot}) [AI]"
                absentee_notifications.append(
                    NotificationLog(recipient=student.user.username, message=msg, channel="STUDENT")
                )
                if student.parent_contact:
                    absentee_notifications.append(
                        NotificationLog(
                            recipient=student.parent_contact,
                            message=f"Ward {student.registration_no} {msg}",
                            channel="PARENT",
                        )
                    )

        AttendanceRecord.objects.bulk_create(records)
        NotificationLog.objects.bulk_create(absentee_notifications)

        messages.success(
            request,
            f"AI attendance saved. Faces detected: {detected_faces_count} | Matched students: {len(matched_student_ids)}",
        )
        return redirect("attendance-report", session_id=session.id)

    selected_id = str(form["course"].value() or initial.get("course") or "")
    enrolled_face_students = []
    if str(selected_id).isdigit():
        enrolled_face_students = list(
            StudentProfile.objects.filter(
                enrollments__course_id=int(selected_id),
                face_profile__is_active=True,
            )
            .select_related("user", "face_profile")
            .distinct()
        )
    return render(
        request,
        "campus_core/attendance_ai_mark.html",
        {
            "form": form,
            "enrolled_face_students": enrolled_face_students,
            "selected_course_id": str(selected_id),
        },
    )


@role_required(ROLE_FACULTY)
def student_course_enroll(request):
    form = StudentEnrollmentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        action = request.POST.get("action", "enroll")
        student_name = " ".join(form.cleaned_data["student_name"].split()).strip()
        registration_no = form.cleaned_data["registration_no"].strip().upper()
        course = form.cleaned_data["course"]
        face_image = form.cleaned_data["face_image"]

        face_encoding = _extract_single_face_encoding(face_image)
        if not face_encoding:
            messages.error(request, "No clear face detected. Please upload a proper front-face image.")
            return render(request, "campus_core/attendance_enroll.html", {"form": form})

        student = StudentProfile.objects.select_related("user").filter(
            registration_no__iexact=registration_no
        ).first()

        if student:
            if not student.user.first_name:
                student.user.first_name = student_name
                student.user.save(update_fields=["first_name"])
        else:
            base_username = re.sub(r"[^a-z0-9]+", "", registration_no.lower())[:20] or "student"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                counter += 1
                username = f"{base_username}{counter}"
            user = User.objects.create(username=username, first_name=student_name)
            student = StudentProfile.objects.create(user=user, registration_no=registration_no)

        face_image.seek(0)
        StudentFaceProfile.objects.update_or_create(
            student=student,
            defaults={
                "face_image": face_image,
                "face_encoding": face_encoding,
                "is_active": True,
            },
        )

        if action == "register_face":
            if course:
                Enrollment.objects.get_or_create(student=student, course=course)
                messages.success(request, f"Face registered and enrolled in {course.code} for {student_name}.")
            else:
                messages.success(request, f"Face registered successfully for {student_name}.")
            return redirect("/attendance/enroll/")

        if not course:
            messages.error(request, "Please select a course to enroll.")
            return render(request, "campus_core/attendance_enroll.html", {"form": form})

        _, created = Enrollment.objects.get_or_create(student=student, course=course)
        if created:
            messages.success(request, f"{student_name} enrolled in {course.code} successfully with face profile.")
        else:
            messages.info(request, f"{student_name} already enrolled in {course.code}. Face profile updated.")
        return redirect(f"/attendance/mark/?course={course.id}")

    return render(request, "campus_core/attendance_enroll.html", {"form": form})


@role_required(ROLE_FACULTY, ROLE_STUDENT, ROLE_VENDOR)
def food_order(request):
    cart = _get_cart(request)
    checkout_form = CartCheckoutForm()
    active_category = request.GET.get("category", "All")
    search_query = request.GET.get("q", "").strip()
    user_role = get_user_role(request.user)
    is_vendor_user = user_role == ROLE_VENDOR
    vendor_stall = None
    vendor_items = []

    if is_vendor_user:
        vendor_stall, _ = FoodStall.objects.get_or_create(
            name=f"{request.user.username} Stall",
            defaults={"is_active": True},
        )

    if request.method == "POST":
        action = request.POST.get("action")
        item_id = request.POST.get("item_id", "")

        if action == "vendor_add_item":
            if not is_vendor_user:
                messages.error(request, "Only vendor can add food items.")
                return redirect("food-order")

            item_name = request.POST.get("item_name", "").strip()
            price_raw = request.POST.get("item_price", "").strip()
            image_url = request.POST.get("item_image_url", "").strip()

            if not item_name:
                messages.error(request, "Enter food item name.")
                return redirect("food-order")

            try:
                item_price = Decimal(price_raw)
            except Exception:
                messages.error(request, "Enter a valid numeric price.")
                return redirect("food-order")

            if item_price <= 0:
                messages.error(request, "Price must be greater than 0.")
                return redirect("food-order")

            item, created = FoodItem.objects.get_or_create(
                stall=vendor_stall,
                name=item_name,
                defaults={
                    "price": item_price,
                    "image_url": image_url,
                },
            )
            if not created:
                item.price = item_price
                item.image_url = image_url
                item.save(update_fields=["price", "image_url"])
                messages.success(request, f"{item_name} updated.")
            else:
                messages.success(request, f"{item_name} added.")
            return redirect("food-order")

        if action == "vendor_remove_item":
            if not is_vendor_user:
                messages.error(request, "Only vendor can remove food items.")
                return redirect("food-order")

            if not item_id.isdigit():
                messages.error(request, "Invalid item selected.")
                return redirect("food-order")

            vendor_item = FoodItem.objects.filter(id=int(item_id), stall=vendor_stall).first()
            if not vendor_item:
                messages.error(request, "Item not found in your stall.")
                return redirect("food-order")

            vendor_item.delete()
            cart.pop(str(item_id), None)
            _save_cart(request, cart)
            messages.info(request, "Food item removed.")
            return redirect("food-order")

        if action == "add" and item_id.isdigit():
            cart[item_id] = min(50, cart.get(item_id, 0) + 1)
            _save_cart(request, cart)
            messages.success(request, "Item added to cart.")
            return redirect("food-order")

        if action == "inc" and item_id in cart:
            cart[item_id] = min(50, cart[item_id] + 1)
            _save_cart(request, cart)
            return redirect("food-order")

        if action == "dec" and item_id in cart:
            cart[item_id] -= 1
            if cart[item_id] <= 0:
                cart.pop(item_id, None)
            _save_cart(request, cart)
            return redirect("food-order")

        if action == "remove" and item_id in cart:
            cart.pop(item_id, None)
            _save_cart(request, cart)
            messages.info(request, "Item removed from cart.")
            return redirect("food-order")

        if action == "clear_cart":
            request.session.pop(CART_SESSION_KEY, None)
            request.session.pop(COUPON_SESSION_KEY, None)
            request.session.modified = True
            messages.info(request, "Cart cleared.")
            return redirect("food-order")

        if action == "apply_coupon":
            coupon = request.POST.get("coupon_code", "").strip().upper()
            if coupon in COUPON_RATES:
                request.session[COUPON_SESSION_KEY] = coupon
                request.session.modified = True
                messages.success(request, f"Coupon {coupon} applied.")
            else:
                request.session.pop(COUPON_SESSION_KEY, None)
                request.session.modified = True
                messages.error(request, "Invalid coupon code. Try SAVE10 or LPU20.")
            return redirect("food-order")

        if action == "checkout":
            checkout_form = CartCheckoutForm(request.POST)
            rows, _, cleaned_cart = _cart_rows(cart)
            if cleaned_cart != cart:
                _save_cart(request, cleaned_cart)
                cart = cleaned_cart

            if not rows:
                messages.error(request, "Cart is empty. Add items before checkout.")
                return redirect("food-order")

            if checkout_form.is_valid():
                student_name = checkout_form.cleaned_data["student_name"]
                break_slot = checkout_form.cleaned_data["break_slot"]
                request.session[CHECKOUT_SESSION_KEY] = {
                    "student_name": student_name,
                    "break_slot": break_slot,
                }
                request.session.modified = True

                messages.info(request, "Checkout captured. Complete payment on Bills page.")
                return redirect("bills-dashboard")

            messages.error(request, "Enter student name and break slot to checkout.")

    categories = [
        {"name": "All", "icon": "A"},
        {"name": "Bakery", "icon": "B"},
        {"name": "Burger", "icon": "G"},
        {"name": "Beverage", "icon": "V"},
        {"name": "Chicken", "icon": "C"},
        {"name": "Pizza", "icon": "P"},
        {"name": "Seafood", "icon": "S"},
    ]

    image_bank = [
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1608039755401-742074f0548d?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
    ]

    popular_items_qs = FoodItem.objects.select_related("stall").order_by("name")
    if search_query:
        popular_items_qs = popular_items_qs.filter(name__icontains=search_query)
    popular_items = list(popular_items_qs[:12])

    for idx, item in enumerate(popular_items):
        item.category = _guess_category(item.name)
        item.preview_image = item.image_url or image_bank[idx % len(image_bank)]
        item.rating = 4.6 + (idx % 4) * 0.1
        item.in_cart_qty = cart.get(str(item.id), 0)

    if active_category != "All":
        popular_items = [item for item in popular_items if item.category == active_category]

    recent_orders = list(FoodOrder.objects.select_related("item").order_by("-ordered_at")[:4])
    for idx, order in enumerate(recent_orders):
        order.preview_image = order.item.image_url or image_bank[(idx + 2) % len(image_bank)]

    summary_items, subtotal, cleaned_cart = _cart_rows(cart)
    if cleaned_cart != cart:
        _save_cart(request, cleaned_cart)

    delivery_fee = Decimal("2.50") if summary_items else Decimal("0.00")
    applied_coupon = request.session.get(COUPON_SESSION_KEY, "")
    discount_rate = COUPON_RATES.get(applied_coupon, Decimal("0.00"))
    discount_amount = (subtotal * discount_rate).quantize(Decimal("0.01"))
    total = subtotal + delivery_fee - discount_amount
    if is_vendor_user and vendor_stall:
        vendor_items = list(FoodItem.objects.filter(stall=vendor_stall).order_by("name"))

    return render(
        request,
        "campus_core/food_order.html",
        {
            "checkout_form": checkout_form,
            "categories": categories,
            "popular_items": popular_items,
            "recent_orders": recent_orders,
            "summary_items": summary_items,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "discount_amount": discount_amount,
            "total": total,
            "cart_count": sum(row["qty"] for row in summary_items),
            "active_category": active_category,
            "search_query": search_query,
            "applied_coupon": applied_coupon,
            "vendor_items": vendor_items,
        },
    )


@role_required(ROLE_FACULTY, ROLE_VENDOR)
def food_analytics(request):
    demand_by_item = (
        FoodOrder.objects.values(item_name=F("item__name"))
        .annotate(total_orders=Sum("quantity"))
        .order_by("-total_orders")
    )
    peak_slots = (
        FoodOrder.objects.values("break_slot")
        .annotate(total_orders=Count("id"))
        .order_by("-total_orders")
    )
    return render(
        request,
        "campus_core/food_analytics.html",
        {
            "demand_by_item": demand_by_item,
            "peak_slots": peak_slots,
        },
    )


@role_required(ROLE_FACULTY, ROLE_STUDENT, ROLE_VENDOR)
def order_history(request):
    payments = PaymentHistory.objects.order_by("-paid_at")
    return render(request, "campus_core/order_history.html", {"payments": payments})


@role_required(ROLE_FACULTY, ROLE_STUDENT, ROLE_VENDOR)
def bills_dashboard(request):
    cart = _get_cart(request)
    payment_methods = ["UPI"]
    upi_methods = ["Google Pay", "PhonePe", "Paytm", "BHIM UPI"]
    checkout_details = request.session.get(CHECKOUT_SESSION_KEY)

    if request.method == "POST":
        action = request.POST.get("action")
        item_id = request.POST.get("item_id", "")

        if action == "add" and item_id.isdigit():
            cart[item_id] = min(50, cart.get(item_id, 0) + 1)
            _save_cart(request, cart)
            return redirect("bills-dashboard")

        if action == "inc" and item_id in cart:
            cart[item_id] = min(50, cart[item_id] + 1)
            _save_cart(request, cart)
            return redirect("bills-dashboard")

        if action == "dec" and item_id in cart:
            cart[item_id] -= 1
            if cart[item_id] <= 0:
                cart.pop(item_id, None)
            _save_cart(request, cart)
            return redirect("bills-dashboard")

        if action == "pay":
            method = request.POST.get("method", "").strip()
            source = request.POST.get("source", "").strip()
            if method not in upi_methods:
                messages.error(request, "Please select a valid payment method.")
                return redirect("bills-dashboard")
            if not cart:
                messages.error(request, "No items in bill to pay.")
                return redirect("bills-dashboard")
            if not checkout_details:
                messages.error(request, "Please checkout from Food Order page first.")
                return redirect("food-order")

            rows, subtotal, cleaned_cart = _cart_rows(cart)
            if cleaned_cart != cart:
                _save_cart(request, cleaned_cart)
                cart = cleaned_cart
                rows, subtotal, _ = _cart_rows(cart)

            student_name = checkout_details.get("student_name", "").strip()
            break_slot = checkout_details.get("break_slot", "LUNCH")
            student = _get_or_create_student_by_name(student_name)
            tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            grand_total = subtotal + tax

            orders = [
                FoodOrder(
                    student=student,
                    item=row["item"],
                    quantity=row["qty"],
                    break_slot=break_slot,
                )
                for row in rows
            ]
            FoodOrder.objects.bulk_create(orders)

            PaymentHistory.objects.create(
                student_name=student_name,
                break_slot=break_slot,
                payment_method=method,
                subtotal=subtotal,
                tax=tax,
                total=grand_total,
                items=[
                    {
                        "name": row["item"].name,
                        "qty": row["qty"],
                        "line_total": str(row["line_total"]),
                    }
                    for row in rows
                ],
            )

            request.session.pop(CART_SESSION_KEY, None)
            request.session.pop(COUPON_SESSION_KEY, None)
            request.session.pop(CHECKOUT_SESSION_KEY, None)
            request.session.modified = True
            if source in {"qr_scan", "qr_scan_auto"}:
                messages.success(request, f"Payment done via {method} (QR scan simulated).")
            else:
                messages.success(request, f"Payment successful via {method}.")
            return redirect("food-order")

    image_bank = [
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1608039755401-742074f0548d?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
    ]

    food_items = list(FoodItem.objects.select_related("stall").order_by("name")[:10])
    for idx, item in enumerate(food_items):
        item.preview_image = item.image_url or image_bank[idx % len(image_bank)]
        item.cart_qty = cart.get(str(item.id), 0)

    summary_items, subtotal, cleaned_cart = _cart_rows(cart)
    if cleaned_cart != cart:
        _save_cart(request, cleaned_cart)
        cart = cleaned_cart

    tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    grand_total = subtotal + tax

    return render(
        request,
        "campus_core/bills_dashboard.html",
        {
            "table_no": "Table-02",
            "bill_time": timezone.localtime(),
            "summary_items": summary_items,
            "subtotal": subtotal,
            "tax": tax,
            "grand_total": grand_total,
            "food_items": food_items,
            "cart_count": sum(row["qty"] for row in summary_items),
            "split_friends": ["AS", "RK", "MN", "PJ"],
            "payment_methods": payment_methods,
            "upi_methods": upi_methods,
            "checkout_details": checkout_details,
        },
    )


@role_required(ROLE_FACULTY)
def resource_dashboard(request):
    blocks = Block.objects.all().prefetch_related("classrooms")
    classrooms = Classroom.objects.all()
    total_capacity = classrooms.aggregate(total=Sum("capacity"))["total"] or 0

    enrolled_count = Enrollment.objects.count()
    capacity_utilization = (enrolled_count / total_capacity * 100) if total_capacity else 0
    total_classrooms = classrooms.count()
    total_blocks = blocks.count()
    total_courses = Course.objects.count()
    total_students = StudentProfile.objects.count()
    total_faculty = User.objects.filter(courses__isnull=False).distinct().count()

    course_utilization = []
    for course in Course.objects.select_related("classroom", "faculty"):
        current_strength = course.enrollments.count()
        room_capacity = course.classroom.capacity if course.classroom else 0
        utilization = (current_strength / room_capacity * 100) if room_capacity else 0
        course_utilization.append(
            {
                "course": course,
                "strength": current_strength,
                "capacity": room_capacity,
                "utilization": utilization,
            }
        )

    faculty_workload = (
        Course.objects.values(faculty_name=F("faculty__username"))
        .annotate(total_courses=Count("id"))
        .order_by("-total_courses")
    )

    return render(
        request,
        "campus_core/resource_dashboard.html",
        {
            "total_capacity": total_capacity,
            "enrolled_count": enrolled_count,
            "capacity_utilization": capacity_utilization,
            "total_classrooms": total_classrooms,
            "total_blocks": total_blocks,
            "total_courses": total_courses,
            "total_students": total_students,
            "total_faculty": total_faculty,
            "blocks": blocks,
            "course_utilization": course_utilization,
            "faculty_workload": faculty_workload,
        },
    )


@role_required(ROLE_FACULTY, ROLE_STUDENT)
def makeup_schedule(request):
    form = MakeupClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        makeup = form.save()
        messages.success(request, f"Make-up class scheduled. Remedial code: {makeup.remedial_code}")
        return redirect("makeup-detail", makeup_id=makeup.id)
    sessions = MakeupClass.objects.select_related("course", "faculty").order_by("-scheduled_for")[:25]
    return render(
        request,
        "campus_core/makeup_schedule.html",
        {
            "form": form,
            "sessions": sessions,
        },
    )


@role_required(ROLE_FACULTY, ROLE_STUDENT)
def makeup_detail(request, makeup_id: int):
    makeup = get_object_or_404(MakeupClass.objects.select_related("course", "faculty"), id=makeup_id)
    entries = makeup.attendance_entries.select_related("student__user")
    present_count = entries.count()
    total_enrolled = Enrollment.objects.filter(course=makeup.course).count()
    return render(
        request,
        "campus_core/makeup_detail.html",
        {
            "makeup": makeup,
            "entries": entries,
            "present_count": present_count,
            "total_enrolled": total_enrolled,
        },
    )


@role_required(ROLE_FACULTY, ROLE_STUDENT)
def makeup_presence_check(request, makeup_id: int):
    makeup = get_object_or_404(MakeupClass.objects.select_related("course", "faculty"), id=makeup_id)
    enrolled_students = (
        StudentProfile.objects.filter(enrollments__course=makeup.course)
        .select_related("user")
        .distinct()
        .order_by("registration_no")
    )
    attendance_rows = MakeupAttendance.objects.filter(makeup_class=makeup).select_related("student")
    attendance_by_student = {row.student_id: row for row in attendance_rows}
    present_ids = set(attendance_by_student.keys())

    rows = []
    for student in enrolled_students:
        rows.append(
            {
                "student": student,
                "is_present": student.id in present_ids,
                "marked_at": attendance_by_student.get(student.id).marked_at if student.id in attendance_by_student else None,
            }
        )

    return render(
        request,
        "campus_core/makeup_presence_check.html",
        {
            "makeup": makeup,
            "rows": rows,
            "present_count": len(present_ids),
            "total_students": len(rows),
            "absent_count": max(0, len(rows) - len(present_ids)),
        },
    )


@role_required(ROLE_FACULTY, ROLE_STUDENT)
def remedial_attendance(request):
    form = RemedialAttendanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        registration_no = form.cleaned_data["registration_no"]
        code = form.cleaned_data["remedial_code"].upper()

        student = get_object_or_404(StudentProfile, registration_no=registration_no)
        makeup = get_object_or_404(MakeupClass, remedial_code=code)

        _, created = MakeupAttendance.objects.get_or_create(makeup_class=makeup, student=student)
        if created:
            messages.success(request, "Remedial attendance marked successfully.")
        else:
            messages.info(request, "Attendance already marked for this remedial code.")
        return redirect("makeup-detail", makeup_id=makeup.id)

    return render(request, "campus_core/remedial_attendance.html", {"form": form})


@role_required(ROLE_FACULTY, ROLE_VENDOR)
def notifications_log(request):
    logs = NotificationLog.objects.order_by("-created_at")[:100]
    return render(request, "campus_core/notifications.html", {"logs": logs})


@role_required(ROLE_FACULTY)
def ai_stub(request):
    recent_sessions = AttendanceSession.objects.order_by("-created_at")[:10]
    slot_counter = Counter(session.time_slot for session in recent_sessions)
    predicted_peak = slot_counter.most_common(1)[0][0] if slot_counter else "LUNCH"
    return render(
        request,
        "campus_core/ai_stub.html",
        {
            "predicted_peak": predicted_peak,
            "generated_at": timezone.now(),
        },
    )
