from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class ComprehensionCheck:
    id: int
    student_id: int
    lesson_id: int
    mentor_userbot_id: int | None
    check_type: str
    raw_response: str
    score: int | None
    ai_reasoning: str | None
    status: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> ComprehensionCheck:
        return cls(
            id=row["id"],
            student_id=row["student_id"],
            lesson_id=row["lesson_id"],
            mentor_userbot_id=row["mentor_userbot_id"],
            check_type=row["check_type"],
            raw_response=row["raw_response"],
            score=row["score"],
            ai_reasoning=row["ai_reasoning"],
            status=row["status"],
        )


class ComprehensionCheckRepository(BaseRepository):
    async def create_pending(
        self,
        student_id: int,
        lesson_id: int,
        raw_response: str,
        mentor_userbot_id: int | None = None,
        check_type: str = "freeform_chat",
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO comprehension_checks
                (student_id, lesson_id, mentor_userbot_id, check_type, raw_response)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, lesson_id, mentor_userbot_id, check_type, raw_response),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def list_pending(self, limit: int = 20) -> list[ComprehensionCheck]:
        cursor = await self._conn.execute(
            "SELECT * FROM comprehension_checks WHERE status = 'pending' ORDER BY created_at LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [ComprehensionCheck.from_row(r) for r in rows]

    async def mark_evaluated(
        self, check_id: int, score: int, reasoning: str, model_used: str
    ) -> None:
        await self._conn.execute(
            """
            UPDATE comprehension_checks
            SET score = ?, ai_reasoning = ?, ai_model_used = ?,
                status = 'evaluated', evaluated_at = datetime('now')
            WHERE id = ?
            """,
            (score, reasoning, model_used, check_id),
        )
        await self._conn.commit()

    async def mark_failed(self, check_id: int) -> None:
        await self._conn.execute(
            "UPDATE comprehension_checks SET status = 'failed' WHERE id = ?", (check_id,)
        )
        await self._conn.commit()

    async def get_latest_score(self, student_id: int, course_id: int) -> int | None:
        cursor = await self._conn.execute(
            """
            SELECT cc.score
            FROM comprehension_checks cc
            JOIN lessons l ON l.id = cc.lesson_id
            WHERE cc.student_id = ? AND l.course_id = ? AND cc.status = 'evaluated'
            ORDER BY cc.evaluated_at DESC
            LIMIT 1
            """,
            (student_id, course_id),
        )
        row = await cursor.fetchone()
        return row["score"] if row else None
