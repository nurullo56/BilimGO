from __future__ import annotations

from typing import Any
from db.database import database


class AdminRepository:
    def __init__(self, conn=None) -> None:
        self._conn = conn

    @property
    def conn(self):
        return self._conn or database.conn

    async def get_overall_stats(self) -> dict[str, Any]:
        c_users = await self.conn.execute("SELECT COUNT(*) as cnt FROM users")
        u_count = (await c_users.fetchone())["cnt"]
        c_sales = await self.conn.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM sales WHERE payment_status = 'paid'"
        )
        s_row = await c_sales.fetchone()
        return {
            "total_users": u_count,
            "total_sales_count": s_row["cnt"],
            "total_revenue": s_row["total"],
        }

    async def get_platform_overview(self) -> dict[str, Any]:
        """Super admin uchun platformaning to'liq ko'rsatkichlari (foydalanuvchilar, mentorlar, savdo, kurslar, kabinetlar, dars ko'rishlar)."""
        # 1. Jami foydalanuvchilar
        c_users = await self.conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE telegram_id IS NOT NULL"
        )
        r_users = await c_users.fetchone()
        total_users = r_users["cnt"] if r_users else 0

        # 2. Faol mentorlar
        c_mentors = await self.conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE role IN ('mentor', 'super_mentor') AND status = 'active'"
        )
        r_mentors = await c_mentors.fetchone()
        total_mentors = r_mentors["cnt"] if r_mentors else 0

        # 3. Aktiv kurslar soni
        c_courses = await self.conn.execute(
            "SELECT COUNT(*) as cnt FROM courses WHERE status = 'published'"
        )
        r_courses = await c_courses.fetchone()
        active_courses = r_courses["cnt"] if r_courses else 0

        # 4. Muvaffaqiyatli to'lovlar va tushum
        c_sales = await self.conn.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM sales WHERE payment_status = 'paid'"
        )
        r_sales = await c_sales.fetchone()
        total_sales_count = r_sales["cnt"] if r_sales else 0
        total_revenue = r_sales["total"] if r_sales else 0

        # 5. Jami kabinetlar va ko'rilgan darslar
        c_cabs = await self.conn.execute("SELECT COUNT(*) as cnt FROM cabinets")
        r_cabs = await c_cabs.fetchone()
        total_cabinets = r_cabs["cnt"] if r_cabs else 0

        c_views = await self.conn.execute("SELECT COUNT(*) as cnt FROM lesson_views")
        r_views = await c_views.fetchone()
        total_views = r_views["cnt"] if r_views else 0

        return {
            "total_users": total_users,
            "active_mentors": total_mentors,
            "active_courses": active_courses,
            "total_sales_count": total_sales_count,
            "total_revenue": total_revenue,
            "total_cabinets": total_cabinets,
            "total_views": total_views,
        }

    async def get_cabinet_students_activity_rows(
        self,
        cabinet_id_clean: int | None = None,
        mentor_id_clean: int | None = None,
    ) -> list[dict]:
        """Kabinet talabalari faolligi va darslarni ko'rish ko'rsatkichlarini bazadan oladi."""
        query = """
        SELECT 
            u.id AS user_id,
            u.full_name,
            u.telegram_id,
            u.phone,
            cm.cabinet_id,
            cm.joined_at,
            c.display_name AS cabinet_name,
            c.branding_config,
            mentor_u.id AS mentor_user_id,
            mentor_u.full_name AS mentor_full_name,
            crs.title AS course_title,
            COUNT(DISTINCT lv.id) AS lessons_watched,
            COALESCE(MAX(lv.completion_percent), 0) AS max_completion,
            COALESCE(AVG(lv.completion_percent), 0) AS avg_completion,
            MAX(lv.started_at) AS last_activity_time
        FROM cabinet_members cm
        JOIN users u ON u.id = cm.user_id
        JOIN cabinets c ON c.id = cm.cabinet_id
        LEFT JOIN license_nodes ln ON ln.id = c.owner_node_id
        LEFT JOIN users mentor_u ON mentor_u.id = ln.owner_user_id
        LEFT JOIN courses crs ON crs.id = ln.course_id
        LEFT JOIN lesson_views lv ON lv.user_id = u.id
        WHERE cm.role_in_cabinet = 'student'
        """
        params = []

        if cabinet_id_clean is not None:
            query += " AND cm.cabinet_id = ?"
            params.append(cabinet_id_clean)

        if mentor_id_clean is not None:
            query += " AND (ln.owner_user_id = ? OR c.owner_node_id IN (SELECT id FROM license_nodes WHERE owner_user_id = ?))"
            params.extend([mentor_id_clean, mentor_id_clean])

        query += " GROUP BY u.id, cm.cabinet_id ORDER BY last_activity_time DESC, u.id ASC"

        cursor = await self.conn.execute(query, tuple(params))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


    async def get_courses_and_counts(self) -> tuple[list[dict], dict[str, int]]:
        """Admin panel va statistika uchun kurslar va auditoriya hisoboti."""
        cursor = await self.conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
        courses = [dict(r) for r in await cursor.fetchall()]

        counts: dict[str, int] = {}

        c_all = await self.conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE status = 'active' AND telegram_id IS NOT NULL"
        )
        r_all = await c_all.fetchone()
        counts["all"] = r_all["cnt"] if r_all else 0

        c_men = await self.conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE role = 'mentor' AND status = 'active' AND telegram_id IS NOT NULL"
        )
        r_men = await c_men.fetchone()
        counts["mentors"] = r_men["cnt"] if r_men else 0

        for c in courses:
            cid = c["id"]
            c_crs = await self.conn.execute(
                """
                SELECT COUNT(DISTINCT u.telegram_id) as cnt
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND u.id IN (
                    SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                    UNION
                    SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
                )
                """,
                (cid, cid),
            )
            r_crs = await c_crs.fetchone()
            all_cnt = r_crs["cnt"] if r_crs else 0
            counts[f"course_{cid}"] = all_cnt
            counts[f"course_all_{cid}"] = all_cnt

            c_std = await self.conn.execute(
                """
                SELECT COUNT(DISTINCT u.telegram_id) as cnt
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active'
                  AND (u.role IS NULL OR u.role NOT IN ('mentor', 'super_mentor', 'admin'))
                  AND u.id IN (
                    SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                    UNION
                    SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
                )
                """,
                (cid, cid),
            )
            r_std = await c_std.fetchone()
            counts[f"course_students_{cid}"] = r_std["cnt"] if r_std else 0

        return courses, counts

    async def get_mentors_list(self) -> list[dict]:
        """Barcha aktiv mentorlar ro'yxati va ularning o'quvchilari soni."""
        cursor = await self.conn.execute(
            """
            SELECT u.id, u.telegram_id, u.full_name,
                   (
                       SELECT COUNT(DISTINCT cm.user_id)
                       FROM cabinet_members cm
                       JOIN cabinets c ON c.id = cm.cabinet_id
                       JOIN license_nodes ln ON ln.id = c.owner_node_id
                       WHERE ln.owner_user_id = u.id AND cm.role_in_cabinet = 'student'
                   ) as students_count
            FROM users u
            WHERE u.role = 'mentor' AND u.status = 'active'
            ORDER BY u.id ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_all_submentors_overview(self) -> list[dict]:
        """Barcha quyi mentorlar ro'yxati (nodasi > 1 bo'lgan) va ularning shogirdlari soni."""
        cursor = await self.conn.execute(
            """
            SELECT
                u.id as user_id, u.full_name, u.telegram_id, u.phone,
                ln.id as node_id, ln.stage, ln.status,
                (SELECT COUNT(*) FROM cabinet_members cm WHERE cm.cabinet_id = cab.id AND cm.role_in_cabinet = 'student') as student_count
            FROM license_nodes ln
            JOIN users u ON u.id = ln.owner_user_id
            LEFT JOIN cabinets cab ON cab.owner_node_id = ln.id
            WHERE ln.id > 1
            ORDER BY ln.id ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


    async def get_mentor_courses_and_counts(self, mentor_id: int) -> tuple[dict, list[dict], dict[str, int]]:
        """Bitta mentorning kurslari va ulardagi o'quvchilar soni."""
        cursor_m = await self.conn.execute(
            "SELECT id, full_name, telegram_id FROM users WHERE id = ?", (mentor_id,)
        )
        mentor_row = await cursor_m.fetchone()
        mentor_info = dict(mentor_row) if mentor_row else {"id": mentor_id, "full_name": f"Mentor #{mentor_id}"}

        cursor_c = await self.conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
        courses = [dict(r) for r in await cursor_c.fetchall()]

        counts: dict[str, int] = {}

        c_all = await self.conn.execute(
            """
            SELECT COUNT(DISTINCT u.telegram_id) as cnt
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
        r_all = await c_all.fetchone()
        counts["mentor_all"] = r_all["cnt"] if r_all else 0
        counts["all"] = counts["mentor_all"]

        for c in courses:
            cid = c["id"]
            c_crs = await self.conn.execute(
                """
                SELECT COUNT(DISTINCT u.telegram_id) as cnt
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
                (mentor_id, cid, mentor_id),
            )
            r_crs = await c_crs.fetchone()
            counts[f"mentor_course_{cid}"] = r_crs["cnt"] if r_crs else 0
            counts[f"course_{cid}"] = counts[f"mentor_course_{cid}"]

        return mentor_info, courses, counts

    async def get_quota_mentors_list(self) -> list[dict]:
        """Quota boshqaruvi uchun quyi mentorlar ro'yxati."""
        cursor = await self.conn.execute(
            """
            SELECT
                u.id as user_id,
                u.full_name,
                u.telegram_id,
                u.phone,
                ln.id as node_id,
                ln.stage,
                ln.status,
                (SELECT COUNT(*) FROM cabinet_members cm WHERE cm.cabinet_id = cab.id AND cm.role_in_cabinet = 'student') as student_count
            FROM license_nodes ln
            JOIN users u ON u.id = ln.owner_user_id
            LEFT JOIN cabinets cab ON cab.owner_node_id = ln.id
            WHERE ln.id > 1
            ORDER BY ln.id ASC
            """
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_mentors_infrastructure_usage_overview(self) -> dict[str, Any]:
        """
        Super Admin uchun barcha faol mentorlar va ularning shogirdlari kesimida:
        - AI tyutor token sarfi (savollar, tokenlar, summa)
        - Server yuki (video streamlar, hosting, summa)
        - Jami infratuzilma xarajatlarini
        hamda platforma Grand Total ko'rsatkichlarini hisoblaydi.
        """
        cursor_m = await self.conn.execute(
            """
            SELECT DISTINCT u.id as user_id, u.full_name, u.telegram_id, u.phone, u.role,
                   ln.id as node_id, ln.stage, ln.status as node_status
            FROM users u
            LEFT JOIN license_nodes ln ON ln.owner_user_id = u.id
            WHERE u.role IN ('mentor', 'super_mentor')
               OR ln.id IS NOT NULL
               OR u.id IN (SELECT DISTINCT mentor_id FROM ai_token_usage)
               OR u.id IN (SELECT DISTINCT mentor_id FROM server_expense_usage)
            ORDER BY u.id ASC
            """
        )
        mentor_rows = await cursor_m.fetchall()

        mentors: list[dict[str, Any]] = []

        for m in mentor_rows:
            mid = m["user_id"]

            cursor_std = await self.conn.execute(
                """
                SELECT COUNT(DISTINCT cm.user_id) as cnt
                FROM cabinet_members cm
                JOIN cabinets c ON c.id = cm.cabinet_id
                JOIN license_nodes ln ON ln.id = c.owner_node_id
                WHERE ln.owner_user_id = ? AND cm.role_in_cabinet = 'student'
                """,
                (mid,),
            )
            r_std = await cursor_std.fetchone()
            student_count = r_std["cnt"] if r_std else 0

            cursor_ai = await self.conn.execute(
                """
                SELECT 
                    COUNT(id) AS total_queries,
                    COALESCE(SUM(total_tokens), 0) AS total_tokens,
                    COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens,
                    COALESCE(SUM(cost_sum), 0.0) AS total_cost_sum
                FROM ai_token_usage
                WHERE mentor_id = ?
                """,
                (mid,),
            )
            ai_row = await cursor_ai.fetchone()
            ai_queries = ai_row["total_queries"] if ai_row else 0
            ai_tokens = ai_row["total_tokens"] if ai_row else 0
            ai_cost = float(ai_row["total_cost_sum"]) if ai_row else 0.0

            cursor_srv = await self.conn.execute(
                """
                SELECT 
                    COUNT(id) AS total_events,
                    COALESCE(SUM(cost_sum), 0.0) AS total_cost_sum,
                    COALESCE(SUM(CASE WHEN expense_type = 'video_bandwidth' THEN units_used ELSE 0 END), 0) AS total_video_views,
                    COALESCE(SUM(CASE WHEN expense_type = 'video_bandwidth' THEN cost_sum ELSE 0 END), 0.0) AS video_bandwidth_cost,
                    COALESCE(SUM(CASE WHEN expense_type = 'hosting_maintenance' THEN cost_sum ELSE 0 END), 0.0) AS hosting_cost
                FROM server_expense_usage
                WHERE mentor_id = ?
                """,
                (mid,),
            )
            srv_row = await cursor_srv.fetchone()
            server_events = srv_row["total_events"] if srv_row else 0
            video_views = int(srv_row["total_video_views"]) if srv_row else 0
            server_cost = float(srv_row["total_cost_sum"]) if srv_row else 0.0

            total_infra_cost = ai_cost + server_cost

            mentors.append({
                "user_id": mid,
                "full_name": m["full_name"] or f"Mentor #{mid}",
                "telegram_id": m["telegram_id"],
                "phone": m["phone"] or "",
                "node_id": m["node_id"],
                "stage": m["stage"] or "limit",
                "student_count": student_count,
                "ai_queries": ai_queries,
                "ai_tokens": ai_tokens,
                "ai_cost": ai_cost,
                "video_views": video_views,
                "server_events": server_events,
                "server_cost": server_cost,
                "total_infra_cost": total_infra_cost,
            })

        cursor_g_ai = await self.conn.execute(
            """
            SELECT 
                COUNT(id) AS total_queries,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(cost_sum), 0.0) AS total_cost_sum
            FROM ai_token_usage
            """
        )
        g_ai = await cursor_g_ai.fetchone()
        grand_ai_queries = g_ai["total_queries"] if g_ai else 0
        grand_ai_tokens = g_ai["total_tokens"] if g_ai else 0
        grand_ai_cost = float(g_ai["total_cost_sum"]) if g_ai else 0.0

        cursor_g_srv = await self.conn.execute(
            """
            SELECT 
                COUNT(id) AS total_events,
                COALESCE(SUM(cost_sum), 0.0) AS total_cost_sum,
                COALESCE(SUM(CASE WHEN expense_type = 'video_bandwidth' THEN units_used ELSE 0 END), 0) AS total_video_views
            FROM server_expense_usage
            """
        )
        g_srv = await cursor_g_srv.fetchone()
        grand_srv_events = g_srv["total_events"] if g_srv else 0
        grand_video_views = int(g_srv["total_video_views"]) if g_srv else 0
        grand_server_cost = float(g_srv["total_cost_sum"]) if g_srv else 0.0

        grand_total = {
            "total_mentors": len(mentors),
            "ai_queries": grand_ai_queries,
            "ai_tokens": grand_ai_tokens,
            "ai_cost": grand_ai_cost,
            "video_views": grand_video_views,
            "server_events": grand_srv_events,
            "server_cost": grand_server_cost,
            "total_infra_cost": grand_ai_cost + grand_server_cost,
        }

        return {
            "mentors": mentors,
            "grand_total": grand_total,
        }
