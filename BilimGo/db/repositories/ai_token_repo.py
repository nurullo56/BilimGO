from __future__ import annotations

from dataclasses import dataclass
import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class AITokenUsage:
    id: int
    mentor_id: int
    student_id: int
    lesson_id: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_sum: float
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> AITokenUsage:
        return cls(
            id=row["id"],
            mentor_id=row["mentor_id"],
            student_id=row["student_id"],
            lesson_id=row["lesson_id"],
            prompt_tokens=row["prompt_tokens"],
            completion_tokens=row["completion_tokens"],
            total_tokens=row["total_tokens"],
            cost_sum=float(row["cost_sum"]),
            created_at=row["created_at"],
        )


class AITokenRepository(BaseRepository):
    async def record_usage(
        self,
        mentor_id: int,
        student_id: int,
        lesson_id: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost_sum: float = 0.0,
    ) -> AITokenUsage:
        total_tokens = prompt_tokens + completion_tokens
        cursor = await self._conn.execute(
            """
            INSERT INTO ai_token_usage (mentor_id, student_id, lesson_id, prompt_tokens, completion_tokens, total_tokens, cost_sum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (mentor_id, student_id, lesson_id, prompt_tokens, completion_tokens, total_tokens, cost_sum),
        )
        await self._conn.commit()
        row_id = cursor.lastrowid
        assert row_id is not None

        c2 = await self._conn.execute("SELECT * FROM ai_token_usage WHERE id = ?", (row_id,))
        row = await c2.fetchone()
        assert row is not None
        return AITokenUsage.from_row(row)

    async def get_mentor_summary(self, mentor_id: int) -> dict:
        cursor = await self._conn.execute(
            """
            SELECT 
                COUNT(id) AS total_queries,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens,
                COALESCE(SUM(cost_sum), 0.0) AS total_cost_sum
            FROM ai_token_usage
            WHERE mentor_id = ?
            """,
            (mentor_id,),
        )
        row = await cursor.fetchone()
        return {
            "total_queries": row["total_queries"] if row else 0,
            "total_tokens": row["total_tokens"] if row else 0,
            "total_prompt_tokens": row["total_prompt_tokens"] if row else 0,
            "total_completion_tokens": row["total_completion_tokens"] if row else 0,
            "total_cost_sum": float(row["total_cost_sum"]) if row else 0.0,
        }

    async def list_mentor_recent_usage(self, mentor_id: int, limit: int = 20) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT u.full_name AS student_name, l.title AS lesson_title,
                   atu.total_tokens, atu.cost_sum, atu.created_at
            FROM ai_token_usage atu
            JOIN users u ON u.id = atu.student_id
            JOIN lessons l ON l.id = atu.lesson_id
            WHERE atu.mentor_id = ?
            ORDER BY atu.id DESC
            LIMIT ?
            """,
            (mentor_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
