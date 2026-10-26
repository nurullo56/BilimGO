from __future__ import annotations
import json
from typing import Any, List, Optional
from db.database import database

class QuizRepository:
    def __init__(self) -> None:
        self.db = database

    async def get_by_lesson_id(self, lesson_id: int) -> List[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM lesson_quizzes WHERE lesson_id = ? ORDER BY order_index ASC",
            (lesson_id,),
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("options_json"), str):
                try:
                    d["options"] = json.loads(d["options_json"])
                except Exception:
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
        if isinstance(d.get("options_json"), str):
            try:
                d["options"] = json.loads(d["options_json"])
            except Exception:
                d["options"] = []
        return d

    async def create_quiz(
        self,
        lesson_id: int,
        question: str,
        options: list[str],
        correct_option_index: int,
        explanation: Optional[str] = None,
        order_index: int = 1,
    ) -> int:
        cursor = await self.db.conn.execute(
            """
            INSERT INTO lesson_quizzes (lesson_id, question, options_json, correct_option_index, explanation, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (lesson_id, question, json.dumps(options, ensure_ascii=False), correct_option_index, explanation, order_index),
        )
        await self.db.conn.commit()
        return cursor.lastrowid

    async def record_attempt(
        self,
        user_id: int,
        quiz_id: int,
        selected_option_index: int,
        is_correct: bool,
    ) -> int:
        cursor = await self.db.conn.execute(
            """
            INSERT INTO user_quiz_attempts (user_id, quiz_id, selected_option_index, is_correct)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, quiz_id, selected_option_index, 1 if is_correct else 0),
        )
        await self.db.conn.commit()
        return cursor.lastrowid

    async def get_user_attempts_for_lesson(self, user_id: int, lesson_id: int) -> List[dict[str, Any]]:
        cursor = await self.db.conn.execute(
            """
            SELECT a.*, q.lesson_id, q.correct_option_index
            FROM user_quiz_attempts a
            JOIN lesson_quizzes q ON q.id = a.quiz_id
            WHERE a.user_id = ? AND q.lesson_id = ?
            ORDER BY a.attempt_time DESC
            """,
            (user_id, lesson_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
