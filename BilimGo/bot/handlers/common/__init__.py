from __future__ import annotations

from bot.handlers.common.cabinet_link import router as cabinet_link_router
from bot.handlers.common.mentor_add import router as mentor_add_router
from bot.handlers.common.profile import router as profile_router
from bot.handlers.common.start import router as start_router

__all__ = [
    "start_router",
    "mentor_add_router",
    "profile_router",
    "cabinet_link_router",
]
