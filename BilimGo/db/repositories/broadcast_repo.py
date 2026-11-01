from __future__ import annotations
from typing import Optional
from db.database import database

class BroadcastRepository:
    def __init__(self) -> None:
        self.db = database

    async def create_broadcast(self, admin_id: int, target_type: str, total_count: int) -> int:
        await self.db.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor = await self.db.conn.execute(
            "INSERT INTO broadcasts (admin_id, target_type, total_count, status) VALUES (?, ?, ?, 'in_progress')",
            (admin_id, target_type, total_count),
        )
        await self.db.conn.commit()
        return cursor.lastrowid

    async def update_broadcast_status(self, broadcast_id: int, sent_count: int, failed_count: int, status: str = "completed") -> None:
        await self.db.conn.execute(
            "UPDATE broadcasts SET sent_count = ?, failed_count = ?, status = ? WHERE id = ?",
            (sent_count, failed_count, status, broadcast_id),
        )
        await self.db.conn.commit()

    async def get_active_user_telegram_ids(self) -> list[int]:
        """Barcha faol foydalanuvchilarning telegram_id ro'yxati."""
        cursor = await self.db.conn.execute(
            "SELECT DISTINCT telegram_id FROM users WHERE status = 'active' AND telegram_id IS NOT NULL"
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    async def get_active_mentor_telegram_ids(self) -> list[int]:
        """Barcha faol mentorlarning telegram_id ro'yxati."""
        cursor = await self.db.conn.execute(
            "SELECT DISTINCT telegram_id FROM users WHERE role = 'mentor' AND status = 'active' AND telegram_id IS NOT NULL"
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    async def get_user_telegram_id_by_id(self, user_id: int) -> list[int]:
        """Muayyan foydalanuvchining telegram_id ro'yxati (1 ta element yoki bo'sh)."""
        cursor = await self.db.conn.execute(
            "SELECT telegram_id FROM users WHERE id = ? AND status = 'active' AND telegram_id IS NOT NULL",
            (user_id,),
        )
        row = await cursor.fetchone()
        return [row["telegram_id"]] if row and row["telegram_id"] else []

    async def get_mentor_course_audience_telegram_ids(self, mentor_id: int, course_id: int) -> list[int]:
        """Muayyan mentorning ma'lum kursdagi shogirdlari telegram_id ro'yxati."""
        cursor = await self.db.conn.execute(
            """
            SELECT DISTINCT u.telegram_id
            FROM users u
            WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                u.id IN (
                    SELECT ag.user_id FROM access_grants ag
                    JOIN sales s ON s.id = ag.granted_via_sale_id
                    JOIN license_nodes ln ON ln.id = s.license_node_id
                    WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                )
                OR u.id IN (
                    SELECT cm.user_id FROM cabinet_members cm
                    JOIN cabinets c ON c.id = cm.cabinet_id
                    JOIN license_nodes ln ON ln.id = c.owner_node_id
                    WHERE ln.owner_user_id = ? AND cm.role_in_cabinet = 'student'
                )
            )
            """,
            (mentor_id, course_id, mentor_id),
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    async def get_mentor_all_audience_telegram_ids(self, mentor_id: int) -> list[int]:
        """Muayyan mentorning barcha shogirdlari telegram_id ro'yxati."""
        cursor = await self.db.conn.execute(
            """
            SELECT DISTINCT u.telegram_id
            FROM users u
            WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                u.id IN (
                    SELECT ag.user_id FROM access_grants ag
                    JOIN sales s ON s.id = ag.granted_via_sale_id
                    JOIN license_nodes ln ON ln.id = s.license_node_id
                    WHERE ln.owner_user_id = ? AND ag.status = 'active'
                )
                OR u.id IN (
                    SELECT cm.user_id FROM cabinet_members cm
                    JOIN cabinets c ON c.id = cm.cabinet_id
                    JOIN license_nodes ln ON ln.id = c.owner_node_id
                    WHERE ln.owner_user_id = ? AND cm.role_in_cabinet = 'student'
                )
            )
            """,
            (mentor_id, mentor_id),
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    async def get_course_students_telegram_ids(self, course_id: int) -> list[int]:
        """Kursdagi oddiy talabalarning (mentor/admin bo'lmagan) telegram_id ro'yxati."""
        cursor = await self.db.conn.execute(
            """
            SELECT DISTINCT u.telegram_id
            FROM users u
            WHERE u.telegram_id IS NOT NULL 
              AND u.status = 'active'
              AND (u.role IS NULL OR u.role NOT IN ('mentor', 'super_mentor', 'admin'))
              AND u.id IN (
                SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                UNION
                SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
            )
            """,
            (course_id, course_id),
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    async def get_course_all_users_telegram_ids(self, course_id: int) -> list[int]:
        """Kursdagi barcha faol foydalanuvchilarning telegram_id ro'yxati."""
        cursor = await self.db.conn.execute(
            """
            SELECT DISTINCT u.telegram_id
            FROM users u
            WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND u.id IN (
                SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                UNION
                SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
            )
            """,
            (course_id, course_id),
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]
