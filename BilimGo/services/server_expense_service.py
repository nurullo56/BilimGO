from __future__ import annotations

import logging
from db.repositories.server_expense_repo import ServerExpenseRepository

logger = logging.getLogger(__name__)

# Standart server tariflari (so'mda)
VIDEO_STREAM_UNIT_COST = 50.0  # Har bir video ko'rish trafigi va relay server xarajati (50 so'm)
ACTIVE_STUDENT_MONTHLY_COST = 1000.0  # Har bir faol shogird hosting va ma'lumotlar bazasi saqlash xarajati (1 000 so'm)


class ServerExpenseService:
    """Har bir shogirdning video stream, hosting va infratuzilma server xarajatlarini
    hisoblab, avtomatik uning ustoziga (mentoriga) yozib boruvchi servis."""

    def __init__(self, server_expense_repo: ServerExpenseRepository) -> None:
        self._repo = server_expense_repo

    async def resolve_student_mentor_id(self, student_id: int) -> int:
        """Talabaning shaxsiy ustozi (mentor_id)ni aniqlaydi."""
        cursor = await self._repo._conn.execute(
            """
            SELECT ln.owner_user_id AS mentor_id
            FROM cabinet_members cm
            JOIN cabinets c ON c.id = cm.cabinet_id
            JOIN license_nodes ln ON ln.id = c.owner_node_id
            WHERE cm.user_id = ?
            LIMIT 1
            """,
            (student_id,),
        )
        row = await cursor.fetchone()
        if row and row["mentor_id"]:
            return row["mentor_id"]
        return 1

    async def track_video_stream(self, student_id: int, lesson_id: int, duration_sec: int = 300) -> None:
        """Shogird video darsni ko'rganida server trafigi va relay xarajatini ustoziga yozadi."""
        mentor_id = await self.resolve_student_mentor_id(student_id)
        cost = VIDEO_STREAM_UNIT_COST

        await self._repo.record_expense(
            mentor_id=mentor_id,
            student_id=student_id,
            expense_type="video_bandwidth",
            units_used=1.0,
            unit_name="stream_view",
            cost_sum=cost,
            description=f"Dars #{lesson_id} video stream trafigi ({duration_sec} soniya)",
        )
        logger.info(
            "Server xarajati yozildi: student_id=%s -> mentor_id=%s, cost=%s so'm",
            student_id, mentor_id, cost,
        )

    async def track_active_student_slot(self, mentor_id: int, student_id: int) -> None:
        """Yangi shogird qo'shilganda yoki oylik faol talaba infratuzilma xarajati."""
        cost = ACTIVE_STUDENT_MONTHLY_COST
        await self._repo.record_expense(
            mentor_id=mentor_id,
            student_id=student_id,
            expense_type="active_student",
            units_used=1.0,
            unit_name="student_month",
            cost_sum=cost,
            description="Shogirdning oylik server va hosting infratuzilma xarajati",
        )

    async def track_custom_maintenance(self, mentor_id: int, amount: float, description: str) -> None:
        """Maxsus server/bot hosting qo'llab-quvvatlash to'lovi."""
        await self._repo.record_expense(
            mentor_id=mentor_id,
            student_id=None,
            expense_type="hosting_maintenance",
            units_used=1.0,
            unit_name="maintenance_fee",
            cost_sum=amount,
            description=description,
        )
