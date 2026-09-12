from __future__ import annotations

import json
import logging

from anthropic import AsyncAnthropic

from core.config import settings
from db.repositories.assessment_criteria_repo import AssessmentCriteriaRepository
from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.user_repo import UserRepository
from services.lesson_completion_service import LessonCompletionService
from services.userbot_client import UserbotClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Sen ta'lim platformasida talabaning dars mavzusini qanchalik \
tushunganini baholovchi yordamchisan. Senga darsning asosiy tushunchalari (mezon) \
va talabaning shu mavzu bo'yicha yozgan javobi beriladi.

Vazifang: talabaning javobini mezon bilan solishtirib, 0 dan 100 gacha ball qo'y \
(100 — mukammal tushungan, 0 — umuman tushunmagan yoki javob mavzuga aloqasiz).

Faqat quyidagi JSON formatda javob ber, boshqa hech qanday matn qo'shma:
{"score": <0-100 butun son>, "reasoning": "<nega shu ball qo'yilgani, 1-2 gap, o'zbek tilida>"}
"""


class AIEvaluationService:
    def __init__(
        self,
        comprehension_repo: ComprehensionCheckRepository,
        criteria_repo: AssessmentCriteriaRepository,
        user_repo: UserRepository | None = None,
        lesson_repo: LessonRepository | None = None,
        lesson_completion_service: LessonCompletionService | None = None,
        userbot_client: UserbotClient | None = None,
        client: AsyncAnthropic | None = None,
    ) -> None:
        self._comprehension_repo = comprehension_repo
        self._criteria_repo = criteria_repo
        self._user_repo = user_repo
        self._lesson_repo = lesson_repo
        self._lesson_completion_service = lesson_completion_service
        self._userbot_client = userbot_client or UserbotClient()
        self._client = client or AsyncAnthropic(api_key=settings.anthropic.api_key)

    async def evaluate_pending_batch(self, limit: int = 10) -> int:
        """Navbatdagi 'pending' tekshiruvlarni baholaydi. Nechta yozuv
        ishlov berilganini qaytaradi."""
        pending = await self._comprehension_repo.list_pending(limit=limit)
        processed = 0
        for check in pending:
            await self._evaluate_one(check)
            processed += 1
        return processed

    async def _evaluate_one(self, check) -> None:
        criteria = await self._criteria_repo.get_by_lesson(check.lesson_id)
        if criteria is None:
            logger.warning(
                "Lesson %s uchun baholash mezoni yo'q, check_id=%s o'tkazib yuborildi",
                check.lesson_id, check.id,
            )
            await self._comprehension_repo.mark_failed(check.id)
            return

        user_prompt = (
            f"Dars mezoni (kutilgan tushunchalar):\n{criteria.key_concepts}\n\n"
            f"Talabaning javobi:\n{check.raw_response}"
        )

        try:
            response = await self._client.messages.create(
                model=settings.anthropic.model,
                max_tokens=300,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            parsed = json.loads(text)
            score = int(parsed["score"])
            reasoning = str(parsed["reasoning"])
        except Exception:
            logger.exception("AI baholashda xato, check_id=%s", check.id)
            await self._comprehension_repo.mark_failed(check.id)
            return

        score = max(0, min(100, score))
        await self._comprehension_repo.mark_evaluated(
            check_id=check.id,
            score=score,
            reasoning=reasoning,
            model_used=settings.anthropic.model,
        )
        logger.info("Baholandi: check_id=%s score=%s", check.id, score)

        # Talabaga baholash natijasini yetkazish
        if self._user_repo and self._lesson_repo:
            try:
                student = await self._user_repo.get_by_id(check.student_id)
                lesson = await self._lesson_repo.get_by_id(check.lesson_id)
                if student and lesson:
                    is_passed = score >= criteria.min_pass_score
                    status_icon = "✅" if is_passed else "⚠️"
                    status_text = "Dars muvaffaqiyatli topshirildi!" if is_passed else "Qayta urinib ko'rishingiz mumkin."
                    feedback_msg = (
                        f"{status_icon} <b>«{lesson.title}» darsi bo'yicha javobingiz baholandi!</b>\n\n"
                        f"🎯 <b>To'plangan ball:</b> {score}/100 (O'tish bali: {criteria.min_pass_score})\n"
                        f"💡 <b>Xulosa:</b> {reasoning}\n\n"
                        f"{status_text}"
                    )
                    await self._userbot_client.send_message(student.telegram_id, feedback_msg)
            except Exception:
                logger.exception("Talabaga baholash xabarini yuborishda xato, check_id=%s", check.id)

        if self._lesson_completion_service and score >= criteria.min_pass_score:
            try:
                await self._lesson_completion_service.handle_lesson_completed(
                    user_id=check.student_id,
                    lesson_id=check.lesson_id,
                )
            except Exception:
                logger.exception("AI baholashdan keyin completion notification yuborishda xato")
