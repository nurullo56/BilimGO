from __future__ import annotations

import aiosqlite


class BaseRepository:
    """Barcha repositorylar uchun umumiy connection egasi."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn
