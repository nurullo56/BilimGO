from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.database import database
from db.repositories.user_repo import UserRepository
from services.quiz_service import QuizService
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])
quiz_service = QuizService()


class QuizAnswerRequest(BaseModel):
    selected_option_index: int


async def _get_current_user_id(telegram_id: int) -> int:
    user_repo = UserRepository(database.conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)
    return user.id


@router.get("/lesson/{lesson_id}")
async def get_lesson_quizzes(lesson_id: int, telegram_id: int = Depends(get_current_telegram_id)):
    return await quiz_service.get_lesson_quizzes(lesson_id, hide_correct=True)


@router.post("/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: int,
    req: QuizAnswerRequest,
    telegram_id: int = Depends(get_current_telegram_id),
):
    user_id = await _get_current_user_id(telegram_id)
    try:
        return await quiz_service.check_answer(user_id, quiz_id, req.selected_option_index)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/lesson/{lesson_id}/status")
async def get_lesson_quiz_status(lesson_id: int, telegram_id: int = Depends(get_current_telegram_id)):
    user_id = await _get_current_user_id(telegram_id)
    return await quiz_service.get_lesson_status(user_id, lesson_id)

