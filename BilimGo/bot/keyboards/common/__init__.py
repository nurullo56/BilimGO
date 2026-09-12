"""
Common keyboards package.
Re-exports all shared keyboard functions for backward compatibility.
"""

from bot.keyboards.common.onboarding_kb import (
    get_direct_course_keyboard,
)
from bot.keyboards.common.mentor_assign_kb import (
    get_mentor_assignment_courses_keyboard,
    get_mentor_tariff_keyboard,
)
from bot.keyboards.common.profile_kb import (
    get_profile_webapp_keyboard,
    get_catalog_webapp_keyboard,
)
from bot.keyboards.common.cabinet_kb import (
    get_cabinets_keyboard,
)

__all__ = [
    # onboarding
    "get_direct_course_keyboard",
    # mentor assign
    "get_mentor_assignment_courses_keyboard",
    "get_mentor_tariff_keyboard",
    # profile
    "get_profile_webapp_keyboard",
    "get_catalog_webapp_keyboard",
    # cabinet
    "get_cabinets_keyboard",
]
