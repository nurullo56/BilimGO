"""
DEPRECATED: Bu fayl backward-compatibility uchun saqlanmoqda.
Yangi kodda quyidagilardan foydalaning:
  from bot.keyboards.student.menu_kb import ...
  from bot.keyboards.student.catalog_kb import ...
  from bot.keyboards.student.payment_kb import ...
"""
from __future__ import annotations

# Re-export everything from modular sub-packages
from bot.keyboards.student.menu_kb import (
    get_phone_request_keyboard,
    get_student_menu,
    get_student_inline_webapp,
    PHONE_REQUEST_KEYBOARD,
    STUDENT_MENU,
)
from bot.keyboards.student.catalog_kb import (
    get_course_list_keyboard,
    get_course_detail_keyboard,
    get_my_courses_progress_keyboard,
)
from bot.keyboards.student.payment_kb import (
    get_checkout_payment_keyboard,
)

__all__ = [
    # menu
    "get_phone_request_keyboard",
    "get_student_menu",
    "get_student_inline_webapp",
    "PHONE_REQUEST_KEYBOARD",
    "STUDENT_MENU",
    # catalog
    "get_course_list_keyboard",
    "get_course_detail_keyboard",
    "get_my_courses_progress_keyboard",
    # payment
    "get_checkout_payment_keyboard",
]
