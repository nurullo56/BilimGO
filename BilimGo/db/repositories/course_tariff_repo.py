from __future__ import annotations
import json
from typing import Any, List, Optional
from db.database import database

class CourseTariffRepository:
    def __init__(self) -> None:
        self.db = database

    async def get_by_course_id(self, course_id: int) -> List[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM course_tariffs WHERE course_id = ? AND is_active = 1 ORDER BY price ASC",
            (course_id,),
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("features_json"), str):
                try:
                    d["features"] = json.loads(d["features_json"])
                except Exception:
                    d["features"] = []
            result.append(d)
        return result

    async def get_by_id(self, tariff_id: int) -> Optional[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM course_tariffs WHERE id = ?", (tariff_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        if isinstance(d.get("features_json"), str):
            try:
                d["features"] = json.loads(d["features_json"])
            except Exception:
                d["features"] = []
        return d
