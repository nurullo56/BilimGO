from __future__ import annotations

from dataclasses import dataclass
import aiosqlite

from db.repositories.base import BaseRepository

TARIFF_LIMITS: dict[str, dict[str, int]] = {
    "standart": {
        "Logistika": 20,
        "Telegram Ads": 6,
        "Konkurs/Aksiya": 5,
        "Saytdan daromad": 3,
        "ChinaSeller": 7,
        "Xitoy": 7,
    },
    "pro": {
        "Logistika": 45,
        "Telegram Ads": 15,
        "Konkurs/Aksiya": 12,
        "Saytdan daromad": 8,
        "ChinaSeller": 15,
        "Xitoy": 15,
    },
    "vip": {
        "Logistika": 100,
        "Telegram Ads": 35,
        "Konkurs/Aksiya": 30,
        "Saytdan daromad": 20,
        "ChinaSeller": 28,
        "Xitoy": 28,
    },
}


@dataclass(slots=True)
class TariffQuota:
    id: int
    node_id: int
    tariff_name: str
    course_title: str
    course_id: int | None
    total_quota: int
    used_quota: int
    created_at: str

    @property
    def remaining(self) -> int:
        return max(0, self.total_quota - self.used_quota)

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> TariffQuota:
        return cls(
            id=row["id"],
            node_id=row["node_id"],
            tariff_name=row["tariff_name"],
            course_title=row["course_title"],
            course_id=row["course_id"],
            total_quota=row["total_quota"],
            used_quota=row["used_quota"],
            created_at=row["created_at"],
        )


class TariffQuotaRepository(BaseRepository):
    async def initialize_quotas_for_tariff(
        self, node_id: int, tariff_name: str
    ) -> list[TariffQuota]:
        """Yangi franshiza olgan mentorga tanlagan tarifi bo'yicha 5 ta kursdan limitlar ochish."""
        tariff_key = tariff_name.lower()
        limits = TARIFF_LIMITS.get(tariff_key, TARIFF_LIMITS["standart"])

        for title, quota in limits.items():
            await self._conn.execute(
                """
                INSERT INTO tariff_quotas (node_id, tariff_name, course_title, total_quota, used_quota)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(node_id, course_title) DO NOTHING
                """,
                (node_id, tariff_key, title, quota),
            )
        await self._conn.commit()
        return await self.list_by_node(node_id)

    async def list_by_node(self, node_id: int) -> list[TariffQuota]:
        cursor = await self._conn.execute(
            "SELECT * FROM tariff_quotas WHERE node_id = ? ORDER BY id ASC", (node_id,)
        )
        rows = await cursor.fetchall()
        return [TariffQuota.from_row(r) for r in rows]

    async def get_quota_for_course(
        self, node_id: int, course_title: str
    ) -> TariffQuota | None:
        cursor = await self._conn.execute(
            """
            SELECT * FROM tariff_quotas
            WHERE node_id = ? AND (course_title LIKE ? OR ? LIKE ('%' || course_title || '%'))
            LIMIT 1
            """,
            (node_id, f"%{course_title}%", course_title),
        )
        row = await cursor.fetchone()
        return TariffQuota.from_row(row) if row else None

    async def consume_quota(self, quota_id: int, autocommit: bool = True) -> bool:
        """1 ta dostup sotilganda ishlatilgan limitni 1 taga oshirish."""
        cursor = await self._conn.execute(
            """
            UPDATE tariff_quotas
            SET used_quota = used_quota + 1
            WHERE id = ? AND used_quota < total_quota
            """,
            (quota_id,),
        )
        if autocommit:
            await self._conn.commit()
        return cursor.rowcount > 0

    async def add_quota_amount(
        self,
        node_id: int,
        course_title: str,
        add_amount: int,
        tariff_name: str = "standart",
        course_id: int | None = None,
    ) -> TariffQuota:
        """Mentorning muayyan kursi uchun bepul dostup limitiga qo'shimcha limit qo'shish."""
        cursor = await self._conn.execute(
            """
            SELECT * FROM tariff_quotas
            WHERE node_id = ? AND (course_title = ? OR course_title LIKE ? OR ? LIKE ('%' || course_title || '%'))
            LIMIT 1
            """,
            (node_id, course_title, f"%{course_title}%", course_title),
        )
        row = await cursor.fetchone()
        if row:
            quota_id = row["id"]
            await self._conn.execute(
                """
                UPDATE tariff_quotas
                SET total_quota = total_quota + ?
                WHERE id = ?
                """,
                (add_amount, quota_id),
            )
            await self._conn.commit()
            updated_cur = await self._conn.execute(
                "SELECT * FROM tariff_quotas WHERE id = ?", (quota_id,)
            )
            updated_row = await updated_cur.fetchone()
            return TariffQuota.from_row(updated_row)
        else:
            cur = await self._conn.execute(
                """
                INSERT INTO tariff_quotas (node_id, tariff_name, course_title, course_id, total_quota, used_quota)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (node_id, tariff_name, course_title, course_id, add_amount),
            )
            await self._conn.commit()
            new_id = cur.lastrowid
            new_cur = await self._conn.execute(
                "SELECT * FROM tariff_quotas WHERE id = ?", (new_id,)
            )
            new_row = await new_cur.fetchone()
            return TariffQuota.from_row(new_row)

    async def set_quota_amount(
        self,
        node_id: int,
        course_title: str,
        new_total: int,
        tariff_name: str = "standart",
        course_id: int | None = None,
    ) -> TariffQuota:
        """Mentorning muayyan kursi uchun limit miqdorini to'g'ridan-to'g'ri belgilash."""
        cursor = await self._conn.execute(
            """
            SELECT * FROM tariff_quotas
            WHERE node_id = ? AND (course_title = ? OR course_title LIKE ? OR ? LIKE ('%' || course_title || '%'))
            LIMIT 1
            """,
            (node_id, course_title, f"%{course_title}%", course_title),
        )
        row = await cursor.fetchone()
        if row:
            quota_id = row["id"]
            await self._conn.execute(
                """
                UPDATE tariff_quotas
                SET total_quota = ?
                WHERE id = ?
                """,
                (new_total, quota_id),
            )
            await self._conn.commit()
            updated_cur = await self._conn.execute(
                "SELECT * FROM tariff_quotas WHERE id = ?", (quota_id,)
            )
            updated_row = await updated_cur.fetchone()
            return TariffQuota.from_row(updated_row)
        else:
            cur = await self._conn.execute(
                """
                INSERT INTO tariff_quotas (node_id, tariff_name, course_title, course_id, total_quota, used_quota)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (node_id, tariff_name, course_title, course_id, new_total),
            )
            await self._conn.commit()
            new_id = cur.lastrowid
            new_cur = await self._conn.execute(
                "SELECT * FROM tariff_quotas WHERE id = ?", (new_id,)
            )
            new_row = await new_cur.fetchone()
            return TariffQuota.from_row(new_row)
