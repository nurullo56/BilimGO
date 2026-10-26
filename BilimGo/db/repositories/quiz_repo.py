from __future__ import annotations
import json
import logging
from typing import Any, List, Optional
from db.database import database

logger = logging.getLogger(__name__)


class QuizRepository:
    def __init__(self) -> None:
        self.db = database

    async def get_by_lesson_id(self, lesson_id: int) -> List[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM lesson_quizzes WHERE lesson_id = ? ORDER BY id ASC",
            (lesson_id,),
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            raw_options = d.get("options") or d.get("options_json")
            if isinstance(raw_options, str):
                try:
                    d["options"] = json.loads(raw_options)
                except Exception:
                    d["options"] = []
            elif not isinstance(d.get("options"), list):
                d["options"] = []
            result.append(d)
        return result

    async def get_by_id(self, quiz_id: int) -> Optional[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM lesson_quizzes WHERE id = ?", (quiz_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        raw_options = d.get("options") or d.get("options_json")
        if isinstance(raw_options, str):
            try:
                d["options"] = json.loads(raw_options)
            except Exception:
                d["options"] = []
        elif not isinstance(d.get("options"), list):
            d["options"] = []
        return d

    async def create_quiz(
        self,
        lesson_id: int,
        question: str,
        options: list[str],
        correct_option_index: int,
        explanation: Optional[str] = None,
        created_by: str = "admin",
    ) -> int:
        cursor = await self.db.conn.execute(
            """
            INSERT INTO lesson_quizzes (lesson_id, question, options, correct_option_index, explanation, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (lesson_id, question, json.dumps(options, ensure_ascii=False), correct_option_index, explanation or "", created_by),
        )
        await self.db.conn.commit()
        return cursor.lastrowid

    async def record_attempt(
        self,
        user_id: int,
        quiz_id: int,
        selected_option_index: int,
        is_correct: bool,
        lesson_id: Optional[int] = None,
    ) -> int:
        # Agar lesson_id berilmagan bo'lsa, quiz dan olamiz
        if lesson_id is None:
            quiz = await self.get_by_id(quiz_id)
            lesson_id = quiz["lesson_id"] if quiz else 1

        cursor = await self.db.conn.execute(
            """
            INSERT INTO lesson_quiz_submissions (user_id, lesson_id, quiz_id, selected_option_index, is_correct)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, lesson_id, quiz_id, selected_option_index, 1 if is_correct else 0),
        )
        await self.db.conn.commit()
        return cursor.lastrowid

    async def get_user_attempts_for_lesson(self, user_id: int, lesson_id: int) -> List[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            """
            SELECT s.*, q.question, q.correct_option_index
            FROM lesson_quiz_submissions s
            JOIN lesson_quizzes q ON q.id = s.quiz_id
            WHERE s.user_id = ? AND s.lesson_id = ?
            ORDER BY s.submitted_at DESC
            """,
            (user_id, lesson_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def mark_lesson_completed(self, user_id: int, lesson_id: int) -> None:
        await self.db.conn.execute(
            """
            INSERT INTO lesson_completions (user_id, lesson_id, quiz_passed, completed_at)
            VALUES (?, ?, 1, datetime('now'))
            ON CONFLICT(user_id, lesson_id) DO UPDATE SET quiz_passed = 1, completed_at = datetime('now')
            """,
            (user_id, lesson_id),
        )
        await self.db.conn.commit()

