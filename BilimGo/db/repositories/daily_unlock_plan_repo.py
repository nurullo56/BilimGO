from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class DailyUnlockPlan:
    id: int
    student_id: int
    course_id: int
    plan_date: str
    max_lessons_allowed: int | None
    comprehension_score_basis: int | None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> DailyUnlockPlan:
        return cls(
            id=row["id"],
            student_id=row["student_id"],
            course_id=row["course_id"],
            plan_date=row["plan_date"],
            max_lessons_allowed=row["max_lessons_allowed"],
            comprehension_score_basis=row["comprehension_score_basis"],
        )


class DailyUnlockPlanRepository(BaseRepository):
    async def get_latest(self, student_id: int, course_id: int) -> DailyUnlockPlan | None:
        cursor = await self._conn.execute(
            """
            SELECT * FROM daily_unlock_plan
            WHERE student_id = ? AND course_id = ?
            ORDER BY plan_date DESC
            LIMIT 1
            """,
            (student_id, course_id),
        )
        row = await cursor.fetchone()
        return DailyUnlockPlan.from_row(row) if row else None

    async def upsert_today(
        self,
        student_id: int,
        course_id: int,
        plan_date: str,
        max_lessons_allowed: int | None,
        comprehension_score_basis: int | None,
    ) -> DailyUnlockPlan:
        await self._conn.execute(
            """
            INSERT INTO daily_unlock_plan
                (student_id, course_id, plan_date, max_lessons_allowed, comprehension_score_basis)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id, course_id, plan_date) DO UPDATE SET
                max_lessons_allowed = excluded.max_lessons_allowed,
                comprehension_score_basis = excluded.comprehension_score_basis
            """,
            (student_id, course_id, plan_date, max_lessons_allowed, comprehension_score_basis),
        )
        await self._conn.commit()

        cursor = await self._conn.execute(
            """
            SELECT * FROM daily_unlock_plan
            WHERE student_id = ? AND course_id = ? AND plan_date = ?
            """,
            (student_id, course_id, plan_date),
        )
        row = await cursor.fetchone()
        assert row is not None
        return DailyUnlockPlan.from_row(row)
