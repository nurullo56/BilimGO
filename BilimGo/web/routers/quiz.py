from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from web.dependencies.auth import get_current_user
from services.quiz_service import QuizService

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])
quiz_service = QuizService()

class QuizAnswerRequest(BaseModel):
    selected_option_index: int

@router.get("/lesson/{lesson_id}")
async def get_lesson_quizzes(lesson_id: int, current_user = Depends(get_current_user)):
    return await quiz_service.get_lesson_quizzes(lesson_id, hide_correct=True)

@router.post("/{quiz_id}/submit")
async def submit_quiz(quiz_id: int, req: QuizAnswerRequest, current_user = Depends(get_current_user)):
    user_id = current_user["id"]
    try:
        return await quiz_service.check_answer(user_id, quiz_id, req.selected_option_index)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.get("/lesson/{lesson_id}/status")
async def get_lesson_quiz_status(lesson_id: int, current_user = Depends(get_current_user)):
    user_id = current_user["id"]
    return await quiz_service.get_lesson_status(user_id, lesson_id)
