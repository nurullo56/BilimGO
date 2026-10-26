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

        lesson_id = quiz.get("lesson_id")
        correct_idx = quiz["correct_option_index"]
        is_correct = (selected_option_index == correct_idx)

        await self.repo.record_attempt(
            user_id=user_id,
            quiz_id=quiz_id,
            selected_option_index=selected_option_index,
            is_correct=is_correct,
            lesson_id=lesson_id,
        )

        status = await self.get_lesson_status(user_id, lesson_id)

        return {
            "quiz_id": quiz_id,
            "is_correct": is_correct,
            "correct_option_index": correct_idx,
            "explanation": quiz.get("explanation") or "",
            "lesson_passed": status.get("passed", False),
        }

    async def get_lesson_status(self, user_id: int, lesson_id: int) -> dict[str, Any]:
        quizzes = await self.repo.get_by_lesson_id(lesson_id)
        if not quizzes:
            return {
                "lesson_id": lesson_id,
                "total_quizzes": 0,
                "passed_quizzes": 0,
                "passed": True,
                "has_quizzes": False,
                "attempts_count": 0,
            }

        attempts = await self.repo.get_user_attempts_for_lesson(user_id, lesson_id)
        passed_quiz_ids = {a["quiz_id"] for a in attempts if a.get("is_correct")}
        all_quiz_ids = {q["id"] for q in quizzes}
        all_passed = all_quiz_ids.issubset(passed_quiz_ids)

        if all_passed and user_id:
            try:
                await self.repo.mark_lesson_completed(user_id, lesson_id)
            except Exception as exc:
                logger.warning("Lesson completion belgilashda xatolik: %s", exc)

        return {
            "lesson_id": lesson_id,
            "total_quizzes": len(quizzes),
            "passed_quizzes": len(passed_quiz_ids),
            "passed": all_passed,
            "has_quizzes": True,
            "attempts_count": len(attempts),
        }
