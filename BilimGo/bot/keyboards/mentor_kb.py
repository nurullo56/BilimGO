"""
DEPRECATED: Bu fayl backward-compatibility uchun saqlanmoqda.
Yangi kodda quyidagilardan foydalaning:
  from bot.keyboards.mentor.menu_kb import ...
  from bot.keyboards.mentor.broadcast_kb import ...
  from bot.keyboards.mentor.live_kb import ...
"""
from __future__ import annotations

# Re-export everything from modular sub-packages
from bot.keyboards.mentor.menu_kb import (
    get_mentor_menu,
    get_mentor_inline_webapp,
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
    "MENTOR_MENU",
    # broadcast
    "get_mentor_broadcast_target_keyboard",
    "get_mentor_broadcast_confirm_keyboard",
    "get_mentor_broadcast_cancel_keyboard",
    # live
    "get_live_course_select_keyboard",
    "get_live_session_scheduled_keyboard",
]