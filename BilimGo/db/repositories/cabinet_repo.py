from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from db.repositories.base import BaseRepository


@dataclass(slots=True)
class Cabinet:
    id: int
    owner_node_id: int
    display_name: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Cabinet:
        return cls(
            id=row["id"],
            owner_node_id=row["owner_node_id"],
            display_name=row["display_name"],
        )


class CabinetRepository(BaseRepository):
    async def get_by_owner_node(self, owner_node_id: int) -> Cabinet | None:
        cursor = await self._conn.execute(
            "SELECT * FROM cabinets WHERE owner_node_id = ?", (owner_node_id,)
        )
        row = await cursor.fetchone()
        return Cabinet.from_row(row) if row else None

    async def create(self, owner_node_id: int, display_name: str) -> Cabinet:
        existing = await self.get_by_owner_node(owner_node_id)
        if existing:
            return existing

        await self._conn.execute(
            """
            INSERT INTO cabinets (owner_node_id, display_name)
            VALUES (?, ?)
            """,
            (owner_node_id, display_name),
        )
        await self._conn.commit()
        cabinet = await self.get_by_owner_node(owner_node_id)
        assert cabinet is not None
        return cabinet

    async def add_member(self, cabinet_id: int, user_id: int, role: str) -> None:
        await self._conn.execute(
            """
            INSERT INTO cabinet_members (cabinet_id, user_id, role_in_cabinet)
            VALUES (?, ?, ?)
            ON CONFLICT(cabinet_id, user_id) DO NOTHING
            """,
            (cabinet_id, user_id, role),
        )
        await self._conn.commit()

    async def is_member(self, cabinet_id: int, user_id: int) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM cabinet_members WHERE cabinet_id = ? AND user_id = ?",
            (cabinet_id, user_id),
        )
        return await cursor.fetchone() is not None

    async def list_students(self, cabinet_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT u.id, u.telegram_id, u.full_name, cm.joined_at
            FROM cabinet_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.cabinet_id = ? AND cm.role_in_cabinet = 'student'
            ORDER BY cm.joined_at DESC
            """,
            (cabinet_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def count_students(self, cabinet_id: int) -> int:
        cursor = await self._conn.execute(
            """
            SELECT COUNT(*) as count
            FROM cabinet_members
            WHERE cabinet_id = ? AND role_in_cabinet = 'student'
            """,
            (cabinet_id,),
        )
        row = await cursor.fetchone()
        return row["count"] if row else 0

    async def list_my_cabinets(self, user_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT c.id, c.display_name, cm.role_in_cabinet
            FROM cabinets c
            JOIN cabinet_members cm ON cm.cabinet_id = c.id
            WHERE cm.user_id = ?
            ORDER BY c.id DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_owned_cabinet_ids(self, owner_user_id: int) -> list[int]:
        """Berilgan foydalanuvchiga tegishli barcha kabinet ID larini bitta so'rov bilan oladi."""
        cursor = await self._conn.execute(
            """
            SELECT c.id 
            FROM cabinets c
            JOIN license_nodes ln ON ln.id = c.owner_node_id
            WHERE ln.owner_user_id = ?
            ORDER BY c.id ASC
            """,
            (owner_user_id,),
        )
        rows = await cursor.fetchall()
        return [r["id"] for r in rows]

    async def get_user_cabinets_with_details(self, user_id: int, is_admin: bool) -> list[dict]:
        """Foydalanuvchining a'zolikdagi (yoki admin bo'lsa barcha) kabinetlarini talabalar soni bilan oladi."""
        if is_admin:
            cursor = await self._conn.execute(
                """
                SELECT c.id, c.display_name, c.branding_config, c.created_at,
                       COALESCE(cm.role_in_cabinet, 'mentor') as role_in_cabinet,
                       (SELECT COUNT(*) FROM cabinet_members WHERE cabinet_id = c.id AND role_in_cabinet = 'student') as students_count
                FROM cabinets c
                LEFT JOIN cabinet_members cm ON cm.cabinet_id = c.id AND cm.user_id = ?
                ORDER BY c.id DESC
                """,
                (user_id,),
            )
        else:
            cursor = await self._conn.execute(
                """
                SELECT c.id, c.display_name, c.branding_config, c.created_at, cm.role_in_cabinet,
                       (SELECT COUNT(*) FROM cabinet_members WHERE cabinet_id = c.id AND role_in_cabinet = 'student') as students_count
                FROM cabinet_members cm
                JOIN cabinets c ON c.id = cm.cabinet_id
                WHERE cm.user_id = ?
                ORDER BY c.id DESC
                """,
                (user_id,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def create_cabinet_record(
        self, owner_node_id: int, display_name: str, branding_config: str | None = None
    ) -> dict:
        """Yangi kabinet yaratadi va yaratilgan yozuvni qaytaradi."""
        cursor = await self._conn.execute(
            """
            INSERT INTO cabinets (owner_node_id, display_name, branding_config)
            VALUES (?, ?, ?)
            RETURNING id, display_name, created_at
            """,
            (owner_node_id, display_name, branding_config),
        )
        row = await cursor.fetchone()
        await self._conn.commit()
        assert row is not None
        return dict(row)

    async def get_branding_config(self, cabinet_id: int) -> str | None:
        """Kabinetning mavjud branding_config satrini oladi."""
        cursor = await self._conn.execute(
            "SELECT branding_config FROM cabinets WHERE id = ?", (cabinet_id,)
        )
        row = await cursor.fetchone()
        return row["branding_config"] if row else None

    async def update_cabinet_branding(
        self, cabinet_id: int, display_name: str, branding_config: str
    ) -> None:
        """Kabinet nomi va brending konfiguratsiyasini yangilaydi."""
        await self._conn.execute(
            "UPDATE cabinets SET display_name = ?, branding_config = ? WHERE id = ?",
            (display_name, branding_config, cabinet_id),
        )
        await self._conn.commit()

    async def delete_cascade(self, cabinet_id: int) -> None:
        """Kabinet va unga tegishli barcha xabar, a'zo va xonalarni kaskadli o'chiradi."""
        await self._conn.execute(
            "DELETE FROM chat_messages WHERE room_id IN (SELECT id FROM chat_rooms WHERE cabinet_id = ?)",
            (cabinet_id,),
        )
        await self._conn.execute(
            "DELETE FROM chat_room_members WHERE room_id IN (SELECT id FROM chat_rooms WHERE cabinet_id = ?)",
            (cabinet_id,),
        )
        await self._conn.execute(
            "DELETE FROM chat_rooms WHERE cabinet_id = ?",
            (cabinet_id,),
        )
        await self._conn.execute(
            "DELETE FROM cabinet_members WHERE cabinet_id = ?",
            (cabinet_id,),
        )
        await self._conn.execute(
            "DELETE FROM cabinets WHERE id = ?",
            (cabinet_id,),
        )
        await self._conn.commit()

    async def get_student_mentor_owner_id(self, student_id: int) -> int | None:
        """Talabaning oxirgi a'zo bo'lgan kabineti orqali uning mentorining owner_user_id sini oladi."""
        cursor = await self._conn.execute(
            """
            SELECT ln.owner_user_id
            FROM cabinet_members cm
            JOIN cabinets c ON c.id = cm.cabinet_id
            JOIN license_nodes ln ON ln.id = c.owner_node_id
            WHERE cm.user_id = ? AND cm.role_in_cabinet = 'student'
            ORDER BY cm.id DESC
            LIMIT 1
            """,
            (student_id,),
        )
        row = await cursor.fetchone()
        return row["owner_user_id"] if row and row["owner_user_id"] else None



