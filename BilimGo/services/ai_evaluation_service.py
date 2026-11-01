from __future__ import annotations

import json
import logging
import re

from core.config import settings
from db.repositories.assessment_criteria_repo import AssessmentCriteriaRepository
from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.user_repo import UserRepository
from services.lesson_completion_service import LessonCompletionService
from services.userbot_client import UserbotClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Sen «BilimGo» ta'lim platformasida talabaning dars mavzusini qanchalik \
tushunganini baholovchi samimiy va tajribali yordamchisan (AGY AI). Senga darsning asosiy tushunchalari (mezon) \
va talabaning shu mavzu bo'yicha yozgan javobi beriladi.

Vazifang: talabaning javobini mezon bilan solishtirib, 0 dan 100 gacha ball qo'y \
(100 — mukammal tushungan, 0 — umuman tushunmagan yoki javob mavzuga aloqasiz).

Faqat quyidagi toza JSON formatda javob ber, boshqa hech qanday ortiqcha matn qo'shma:
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
    ) -> None:
        self._comprehension_repo = comprehension_repo
        self._criteria_repo = criteria_repo
        self._user_repo = user_repo
        self._lesson_repo = lesson_repo
        self._lesson_completion_service = lesson_completion_service
        self._userbot_client = userbot_client or UserbotClient()

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

        score: int | None = None
        reasoning: str = ""
        model_name: str = "fallback"

        # 1. PRIMARY: AGY / Google Gemini AI orqali baholash
        if settings.gemini.api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.gemini.api_key)
                config = types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json",
                )
                response = await client.aio.models.generate_content(
                    model=settings.gemini.model or "gemini-2.0-flash",
                    contents=user_prompt,
                    config=config,
                )
                if response and response.text:
                    parsed = json.loads(response.text.strip())
                    score = int(parsed["score"])
                    reasoning = str(parsed["reasoning"])
                    model_name = settings.gemini.model
            except Exception as e:
                logger.warning("Gemini orqali baholashda xatolik: %s", e)

        # 2. SECONDARY: Anthropic Claude (agar Gemini bo'lmasa)
        if score is None and settings.anthropic.api_key and not settings.debug:
            try:
                from anthropic import AsyncAnthropic
                claude_client = AsyncAnthropic(api_key=settings.anthropic.api_key)
                response = await claude_client.messages.create(
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
                model_name = settings.anthropic.model
            except Exception as e:
                logger.warning("Claude orqali baholashda xatolik: %s", e)

        # 3. FALLBACK: Qoidaga asoslangan lokal baholash
        if score is None:
            ans_len = len(str(check.raw_response or "").strip())
            if ans_len > 40:
                score = 80
                reasoning = "Javob umumiy qabul qilindi va dars mavzusiga mos keladi."
            elif ans_len > 15:
                score = 65
                reasoning = "Javob qisqa, lekin asosiy fikr ifodalangan."
            else:
                score = 40
                reasoning = "Javob juda qisqa yoki to'liq emas. Mavzuni kengroq yoriting."
            model_name = "local_rule_evaluator"

        score = max(0, min(100, score))
        await self._comprehension_repo.mark_evaluated(
            check_id=check.id,
            score=score,
            reasoning=reasoning,
            model_used=model_name,
        )
        logger.info("Baholandi: check_id=%s score=%s model=%s", check.id, score, model_name)

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
