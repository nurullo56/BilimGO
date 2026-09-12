from __future__ import annotations

from db.repositories.engagement_repo import EngagementRepository, NudgeRepository

# Bosqichlar bo'yicha eskalatsiya xabar shablonlari
NUDGE_STEPS: dict[int, str] = {
    1: "Salom{name}! 📚 Darslaringiz sizni kutmoqda — bugun ozgina vaqt ajratib, o'quv jarayonini davom ettiramizmi? 🙂",
    2: "Salom{name}! ⏳ 2 kundan beri platformada faol ko'rinmaysiz. O'rganishda davomiylik juda muhim. Bugun yangi darsni ko'ramizmi?",
    3: "Salom{name}! 💬 Mentoringiz sizni kutmoqda. Biror tushunmovchilik yoki savollar bo'lsa, chat orqali bemalol murojaat qiling!",
    4: "Salom{name}! 🚀 Kursni davom ettirish uchun platforma har doim sizga ochiq. Har qanday katta natija kichik va davomiy qadamlardan boshlanadi!",
}
MAX_NUDGE_STEPS = max(NUDGE_STEPS)


class EngagementMonitorService:
    def __init__(
        self, engagement_repo: EngagementRepository, nudge_repo: NudgeRepository
    ) -> None:
        self._engagement_repo = engagement_repo
        self._nudge_repo = nudge_repo

    async def touch_activity(self, user_id: int) -> None:
        """Talaba faol harakat qilganda chaqiriladi (masalan video ko'rganda)."""
        await self._engagement_repo.touch(user_id)
        await self._nudge_repo.stop_campaign(user_id)

    async def scan_and_advance(self, inactivity_threshold_hours: int = 24) -> list[tuple[int, str]]:
        """Faolsiz foydalanuvchilarni topadi, kampaniyani boshlaydi/oshiradi.
        Yuborilishi kerak bo'lgan (user_id, xabar matni) juftliklarini qaytaradi —
        haqiqiy yuborish chaqiruvchi tomonda (bot orqali) amalga oshiriladi."""
        inactive_user_ids = await self._engagement_repo.list_inactive_since(
            inactivity_threshold_hours
        )
        to_send: list[tuple[int, str]] = []

        for user_id in inactive_user_ids:
            campaign = await self._nudge_repo.get_active_campaign(user_id)

            if campaign is None:
                campaign_id = await self._nudge_repo.start_campaign(user_id)
                next_step = 1
            else:
                if campaign.current_step >= MAX_NUDGE_STEPS:
                    await self._nudge_repo.exhaust_campaign(campaign.id)
                    continue
                campaign_id = campaign.id
                next_step = campaign.current_step + 1

            await self._nudge_repo.advance_step(campaign_id, next_step)
            to_send.append((user_id, NUDGE_STEPS[next_step]))

        return to_send
