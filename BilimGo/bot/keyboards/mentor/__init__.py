"""
Mentor keyboards package.
Re-exports all mentor keyboard functions for backward compatibility.
"""

from bot.keyboards.mentor.menu_kb import (
    get_mentor_menu,
    get_mentor_inline_webapp,
    get_mentor_card_manage_keyboard,
    MENTOR_MENU,
)
from bot.keyboards.mentor.broadcast_kb import (
    get_mentor_broadcast_target_keyboard,
    get_mentor_broadcast_confirm_keyboard,
    get_mentor_broadcast_cancel_keyboard,
)
from bot.keyboards.mentor.live_kb import (
    get_live_course_select_keyboard,
    get_live_session_scheduled_keyboard,
)

__all__ = [
    # menu
    "get_mentor_menu",
    "get_mentor_inline_webapp",
    "get_mentor_card_manage_keyboard",
    "MENTOR_MENU",
    # broadcast
    "get_mentor_broadcast_target_keyboard",
    "get_mentor_broadcast_confirm_keyboard",
    "get_mentor_broadcast_cancel_keyboard",
    # live
    "get_live_course_select_keyboard",
    "get_live_session_scheduled_keyboard",
]
