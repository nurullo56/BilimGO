from __future__ import annotations

from typing import Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from db.database import database
from db.repositories.ai_token_repo import AITokenRepository
from db.repositories.assessment_criteria_repo import AssessmentCriteriaRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.user_repo import UserRepository
from services.ai_tutor_service import AITutorService
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai_tutor"])


class AIChatRequest(BaseModel):
    lesson_id: int | str | None = None
    message: str | None = None
    question: str | None = None
    lessonTitle: str | None = None
    courseTitle: str | None = None
    lessonDescription: str | None = None
    history: list[dict[str, Any]] = []


def _build_ai_tutor_service() -> AITutorService:
    conn = database.conn
    return AITutorService(
        ai_token_repo=AITokenRepository(conn),
        lesson_repo=LessonRepository(conn),
        course_repo=CourseRepository(conn),
        criteria_repo=AssessmentCriteriaRepository(conn),
        user_repo=UserRepository(conn),
    )


@router.post("/lesson-chat")
@router.post("/ask-lesson")
async def chat_with_lesson_ai(
    body: AIChatRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """Video dars tagidagi AI Agent — talabaning dars bo'yicha savoliga javob beradi."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    service = _build_ai_tutor_service()

    # Parse numeric lesson_id if provided or search by title
    resolved_lesson_id = 1
    if body.lesson_id:
        try:
            # Handle e.g. "l-101" or "101" or 101
            raw_id = str(body.lesson_id).replace("l-", "")
            resolved_lesson_id = int(raw_id)
        except ValueError:
            resolved_lesson_id = 1

    user_msg = body.message or body.question or ""
    if not user_msg:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Savol matni bo'sh bo'lishi mumkin emas")

    # Format history correctly
    formatted_history = []
    for h in body.history:
        sender = h.get("sender") or h.get("role", "user")
        text = h.get("text") or h.get("content", "")
        role = "assistant" if sender in ("assistant", "bot", "ai") else "user"
        if text:
            formatted_history.append({"role": role, "content": text})

    try:
        result = await service.ask_lesson_ai(
            student_id=user.id,
            lesson_id=resolved_lesson_id,
            user_message=user_msg,
            history=formatted_history,
        )
        reply = result.get("reply", "")
        return {
            **result,
            "answer": reply,
            "reply": reply,
        }
    except Exception as exc:
        logger.exception("AI Agent bilan muloqotda xato")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/mentor-token-stats")
async def get_mentor_token_stats(
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """Mentor uchun shogirdlari ishlatgan AI tokenlar hisoboti."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    token_repo = AITokenRepository(conn)

    summary = await token_repo.get_mentor_summary(user.id)
    recent = await token_repo.list_mentor_recent_usage(user.id, limit=15)
    return {
        "summary": summary,
        "recent_usage": recent,
    }
