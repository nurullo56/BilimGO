from __future__ import annotations

from db.repositories.base import BaseRepository


class LessonViewRepository(BaseRepository):
    async def start_view(
        self, user_id: int, lesson_id: int, delivery_token_id: int | None = None
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO lesson_views (user_id, lesson_id, delivery_token_id)
            VALUES (?, ?, ?)
            """,
            (user_id, lesson_id, delivery_token_id),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_latest_view_id(self, user_id: int, lesson_id: int) -> int | None:
        """Foydalanuvchining dars uchun eng oxirgi ko'rish yozuvi ID sini oladi."""
        cursor = await self._conn.execute(
            """
            SELECT id FROM lesson_views
            WHERE user_id = ? AND lesson_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, lesson_id),
        )
        row = await cursor.fetchone()
        return row["id"] if row else None

    async def update_progress(
        self, view_id: int, watch_duration_sec: int, completion_percent: int
    ) -> None:
        completed_at_clause = ", completed_at = COALESCE(completed_at, datetime('now'))" if completion_percent >= 90 else ""
        await self._conn.execute(
            f"""
            UPDATE lesson_views
            SET watch_duration_sec = MAX(watch_duration_sec, ?),
                completion_percent = MAX(completion_percent, ?){completed_at_clause}
            WHERE id = ?
            """,
            (watch_duration_sec, completion_percent, view_id),
        )
        await self._conn.commit()

    async def student_progress_for_course(self, user_id: int, course_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT l.id AS lesson_id, l.title,
                   COALESCE(MAX(lv.completion_percent), 0) AS completion_percent,
                   COALESCE(MAX(lv.watch_duration_sec), 0) AS watch_duration_sec,
                   MAX(lv.started_at) AS started_at
            FROM lessons l
            LEFT JOIN lesson_views lv ON lv.lesson_id = l.id AND lv.user_id = ?
            WHERE l.course_id = ?
            GROUP BY l.id, l.title, l.order_index
            ORDER BY l.order_index
            """,
            (user_id, course_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def mentor_students_activity(self, cabinet_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT u.id AS user_id, u.full_name, u.telegram_id,
                   COUNT(lv.id) AS lessons_watched,
                   MAX(lv.started_at) AS last_activity
            FROM cabinet_members cm
            JOIN users u ON u.id = cm.user_id
            LEFT JOIN lesson_views lv ON lv.user_id = u.id
            WHERE cm.cabinet_id = ? AND cm.role_in_cabinet = 'student'
            GROUP BY u.id
            ORDER BY last_activity DESC
            """,
            (cabinet_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_study_stats(self, user_id: int) -> dict:
        """Foydalanuvchining darslarni o'zlashtirish va ko'rish vaqti statistikasini oladi."""
        cursor = await self._conn.execute(
            """
            SELECT 
                COUNT(CASE WHEN completion_percent >= 90 THEN 1 END) as completed_count,
                COALESCE(SUM(watch_duration_sec), 0) as total_watch_sec
            FROM lesson_views
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        completed_count = row["completed_count"] if row else 0
        total_sec = row["total_watch_sec"] if row else 0
        return {
            "completed_lessons": completed_count,
            "total_study_minutes": round(total_sec / 60),
        }

    async def get_streak_days(self, user_id: int) -> int:
        """Oxirgi 7 kundagi faol o'qish kunlari sonini (streak) oladi."""
        cursor = await self._conn.execute(
            """
            SELECT COUNT(DISTINCT date(started_at)) as streak
            FROM lesson_views
            WHERE user_id = ? AND started_at >= datetime('now', '-7 days')
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return row["streak"] if row else 1

    async def get_daily_activity_map(self, user_id: int, days: int = 30) -> dict[str, dict]:
        """Oxirgi kunlar bo'yicha kunlik faollik xaritasini oladi."""
        cursor = await self._conn.execute(
            f"""
            SELECT 
                date(started_at) as view_date,
                COUNT(id) as views_count,
                COALESCE(SUM(watch_duration_sec), 0) as total_sec
            FROM lesson_views
            WHERE user_id = ? AND started_at >= datetime('now', '-{days} days')
            GROUP BY date(started_at)
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return {r["view_date"]: dict(r) for r in rows}
