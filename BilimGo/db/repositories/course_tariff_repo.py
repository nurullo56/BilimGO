from __future__ import annotations

import json
from typing import Any, List, Optional
from db.database import database


class CourseTariffRepository:
    def __init__(self, conn=None) -> None:
        self._conn = conn or database.conn

    async def get_by_course_id(self, course_id: int) -> List[dict[str, Any]]:
        cursor = await self._conn.execute(
            "SELECT * FROM course_tariffs WHERE course_id = ? ORDER BY price ASC",
            (course_id,),
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            raw_features = d.get("features") or d.get("features_json")
            if isinstance(raw_features, str):
                try:
                    d["features"] = json.loads(raw_features)
                except Exception:
                    d["features"] = []
            elif not isinstance(d.get("features"), list):
                d["features"] = []
            result.append(d)
        return result

    async def get_by_id(self, tariff_id: int) -> Optional[dict[str, Any]]:
        cursor = await self._conn.execute(
            "SELECT * FROM course_tariffs WHERE id = ?", (tariff_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        raw_features = d.get("features") or d.get("features_json")
        if isinstance(raw_features, str):
            try:
                d["features"] = json.loads(raw_features)
            except Exception:
                d["features"] = []
        elif not isinstance(d.get("features"), list):
            d["features"] = []
        return d
