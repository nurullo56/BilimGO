from __future__ import annotations
import logging
from typing import Any, List, Optional
from db.repositories.quiz_repo import QuizRepository

logger = logging.getLogger(__name__)

class QuizService:
    def __init__(self, quiz_repo: Optional[QuizRepository] = None) -> None:
        self.repo = quiz_repo or QuizRepository()

    async def get_lesson_quizzes(self, lesson_id: int, hide_correct: bool = True) -> List[dict[str, Any]]:
        quizzes = await self.repo.get_by_lesson_id(lesson_id)
        if hide_correct:
            for q in quizzes:
                q.pop("correct_option_index", None)
                q.pop("explanation", None)
        return quizzes

    async def check_answer(
        self, user_id: int, quiz_id: int, selected_option_index: int
    ) -> dict[str, Any]:
        quiz = await self.repo.get_by_id(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz topilmadi: {quiz_id}")

        correct_idx = quiz["correct_option_index"]
        is_correct = (selected_option_index == correct_idx)

        await self.repo.record_attempt(
            user_id=user_id,
            quiz_id=quiz_id,
            selected_option_index=selected_option_index,
            is_correct=is_correct,
        )

        return {
            "quiz_id": quiz_id,
            "is_correct": is_correct,
            "correct_option_index": correct_idx,
            "explanation": quiz.get("explanation") or "",
        }

    async def get_lesson_status(self, user_id: int, lesson_id: int) -> dict[str, Any]:
        quizzes = await self.repo.get_by_lesson_id(lesson_id)
        attempts = await self.repo.get_user_attempts_for_lesson(user_id, lesson_id)
        
        total_quizzes = len(quizzes)
        correct_count = sum(1 for a in attempts if a["is_correct"])
        
        return {
            "lesson_id": lesson_id,
            "total_quizzes": total_quizzes,
            "passed": (correct_count >= total_quizzes) if total_quizzes > 0 else True,
            "attempts_count": len(attempts),
        }
