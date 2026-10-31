"""
Admin keyboards package.
Re-exports all admin keyboard functions for backward compatibility.
"""

from bot.keyboards.admin.menu_kb import (
    get_admin_menu,
    get_admin_inline_webapp,
    get_admin_panel_keyboard,
    ADMIN_MENU,
)
from bot.keyboards.admin.broadcast_kb import (
    get_broadcast_target_keyboard,
    get_broadcast_course_audience_keyboard,
    get_broadcast_mentors_keyboard,
    get_broadcast_mentor_courses_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_cancel_keyboard,
)
from bot.keyboards.admin.quota_kb import (
    get_quota_mentors_keyboard,
    get_quota_courses_keyboard,
    get_quota_amount_keyboard,
)

__all__ = [
    # menu
    "get_admin_menu",
    "get_admin_inline_webapp",
    "get_admin_panel_keyboard",
    "ADMIN_MENU",
    # broadcast
    "get_broadcast_target_keyboard",
    "get_broadcast_course_audience_keyboard",
    "get_broadcast_mentors_keyboard",
    "get_broadcast_mentor_courses_keyboard",
    "get_broadcast_confirm_keyboard",
    "get_broadcast_cancel_keyboard",
    # quota
    "get_quota_mentors_keyboard",
    "get_quota_courses_keyboard",
    "get_quota_amount_keyboard",
]
