"""
DEPRECATED: Bu fayl backward-compatibility va router re-export uchun saqlanmoqda.
Yangi modulli fayllar:
- start.py
- mentor_add.py
- profile.py
- _utils.py
"""
from __future__ import annotations

from bot.handlers.common.start import router

__all__ = ["router"]
