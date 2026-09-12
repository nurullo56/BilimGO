from __future__ import annotations

from datetime import date

from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
from db.repositories.daily_unlock_plan_repo import DailyUnlockPlan, DailyUnlockPlanRepository
from db.repositories.unlock_tier_repo import UnlockTierRuleRepository

DEFAULT_SCORE_FOR_NEW_STUDENT = 0


class AdaptiveUnlockService:
    """Talabaning eng so'nggi tushunish balliga qarab, kursda nechta dars
    ochiq bo'lishini kunma-kun kengaytirib boradi (kumulyativ cheklov)."""

    def __init__(
        self,
        plan_repo: DailyUnlockPlanRepository,
        tier_repo: UnlockTierRuleRepository,
        comprehension_repo: ComprehensionCheckRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._tier_repo = tier_repo
        self._comprehension_repo = comprehension_repo

    async def get_effective_limit(self, student_id: int, course_id: int) -> int | None:
        """None = cheklovsiz. Aks holda — talaba shu kursda jami nechta
        darsga (order_index bo'yicha) kirishi mumkinligini qaytaradi."""
        today = date.today().isoformat()
        latest_plan = await self._plan_repo.get_latest(student_id, course_id)

        if latest_plan is not None and latest_plan.plan_date == today:
            return latest_plan.max_lessons_allowed

        return await self._advance_plan(student_id, course_id, today, latest_plan)

    async def _advance_plan(
        self,
        student_id: int,
        course_id: int,
        today: str,
        previous_plan: DailyUnlockPlan | None,
    ) -> int | None:
        if previous_plan is not None and previous_plan.max_lessons_allowed is None:
            # Avvalgi kunlardanoq cheklovsiz bo'lgan — shunday qoladi
            new_limit = None
            score = previous_plan.comprehension_score_basis
        else:
            score = await self._comprehension_repo.get_latest_score(student_id, course_id)
            if score is None:
                score = DEFAULT_SCORE_FOR_NEW_STUDENT

            tier = await self._tier_repo.find_tier(course_id, score)
            daily_limit = tier.daily_lesson_limit if tier is not None else 1

            previous_cumulative = previous_plan.max_lessons_allowed if previous_plan else 0
            new_limit = None if daily_limit is None else previous_cumulative + daily_limit

        plan = await self._plan_repo.upsert_today(
            student_id=student_id,
            course_id=course_id,
            plan_date=today,
            max_lessons_allowed=new_limit,
            comprehension_score_basis=score,
        )
        return plan.max_lessons_allowed
