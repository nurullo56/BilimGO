from __future__ import annotations

from bot.handlers.admin.statistics import router as stats_router
from bot.handlers.admin.broadcast import router as broadcast_router
from bot.handlers.admin.quota import router as quota_router
from bot.handlers.admin.course_waitlist import router as course_waitlist_router

__all__ = ["stats_router", "broadcast_router", "quota_router", "course_waitlist_router"]
