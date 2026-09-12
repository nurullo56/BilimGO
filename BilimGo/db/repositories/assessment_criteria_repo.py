from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class AssessmentCriteria:
    lesson_id: int
    key_concepts: str
    min_pass_score: int

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> AssessmentCriteria:
        return cls(
            lesson_id=row["lesson_id"],
            key_concepts=row["key_concepts"],
            min_pass_score=row["min_pass_score"],
        )


class AssessmentCriteriaRepository(BaseRepository):
    async def get_by_lesson(self, lesson_id: int) -> AssessmentCriteria | None:
        cursor = await self._conn.execute(
            "SELECT * FROM lesson_assessment_criteria WHERE lesson_id = ?", (lesson_id,)
        )
        row = await cursor.fetchone()
        return AssessmentCriteria.from_row(row) if row else None

    async def upsert(self, lesson_id: int, key_concepts: str, min_pass_score: int = 70) -> None:
        await self._conn.execute(
            """
            INSERT INTO lesson_assessment_criteria (lesson_id, key_concepts, min_pass_score)
            VALUES (?, ?, ?)
            ON CONFLICT(lesson_id) DO UPDATE SET
                key_concepts = excluded.key_concepts,
                min_pass_score = excluded.min_pass_score
            """,
            (lesson_id, key_concepts, min_pass_score),
        )
        await self._conn.commit()
