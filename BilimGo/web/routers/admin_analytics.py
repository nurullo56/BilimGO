from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Query

from db.database import database
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.user_repo import UserRepository
from services.analytics_service import AnalyticsService
from web.dependencies.auth import get_current_telegram_id

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
@router.get("/admin/overview")
async def get_platform_admin_overview(
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """Super admin uchun platformaning to'liq ko'rsatkichlari (foydalanuvchilar, savdo, kurslar)."""
    conn = database.conn

    # 1. Jami foydalanuvchilar
    c_users = await conn.execute("SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE telegram_id IS NOT NULL")
    r_users = await c_users.fetchone()
    total_users = r_users["cnt"] if r_users else 0

    # 2. Faol mentorlar
    c_mentors = await conn.execute(
        "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE role IN ('mentor', 'super_mentor') AND status = 'active'"
    )
    r_mentors = await c_mentors.fetchone()
    total_mentors = r_mentors["cnt"] if r_mentors else 0

    # 3. Aktiv kurslar soni
    c_courses = await conn.execute("SELECT COUNT(*) as cnt FROM courses WHERE status = 'published'")
    r_courses = await c_courses.fetchone()
    active_courses = r_courses["cnt"] if r_courses else 0

    # 4. Muvaffaqiyatli to'lovlar va tushum
    c_sales = await conn.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM sales WHERE payment_status = 'paid'"
    )
    r_sales = await c_sales.fetchone()
    total_sales_count = r_sales["cnt"] if r_sales else 0
    total_revenue = r_sales["total"] if r_sales else 0

    # 5. Jami kabinetlar va ko'rilgan darslar
    c_cabs = await conn.execute("SELECT COUNT(*) as cnt FROM cabinets")
    r_cabs = await c_cabs.fetchone()
    total_cabinets = r_cabs["cnt"] if r_cabs else 0

    c_views = await conn.execute("SELECT COUNT(*) as cnt FROM lesson_views")
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


@router.get("/courses/{course_id}/my-progress")
async def my_progress(
    course_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> list[dict]:
    clean_course_id = int(str(course_id).replace("course-", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    service = AnalyticsService(LessonViewRepository(database.conn))
    return await service.get_student_progress(user.id, clean_course_id)


@router.get("/cabinets/activity")
@router.get("/cabinets/{cabinet_id}/activity")
async def get_cabinet_students_activity(
    cabinet_id: str | int | None = None,
    mentor_id: str | int | None = None,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict]:
    """Super admin / mentor uchun platformadagi o'quvchilar faolligi va darslarni o'zlashtirish statistikasi."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)

    # Base query for all students in cabinet_members
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

    clean_cab_id = None
    if cabinet_id and str(cabinet_id) != "all" and str(cabinet_id) != "":
        try:
            clean_cab_id = int(str(cabinet_id).replace("cab-", ""))
            query += " AND cm.cabinet_id = ?"
            params.append(clean_cab_id)
        except ValueError as exc:
            import logging
            logging.warning("Kutilgan xato yuz berdi (%s): %s", 'ValueError', exc)

    clean_mentor_id = None
    if mentor_id and str(mentor_id) != "all" and str(mentor_id) != "":
        try:
            clean_mentor_id = int(str(mentor_id).replace("mentor-", ""))
            query += " AND (ln.owner_user_id = ? OR c.owner_node_id IN (SELECT id FROM license_nodes WHERE owner_user_id = ?))"
            params.extend([clean_mentor_id, clean_mentor_id])
        except ValueError as exc:
            import logging
            logging.warning("Mentor ID format xatosi: %s", exc)

    query += " GROUP BY u.id, cm.cabinet_id ORDER BY last_activity_time DESC, u.id ASC"

    cursor = await conn.execute(query, tuple(params))
    rows = await cursor.fetchall()

    results = []
    for r in rows:
        branding = {}
        if r["branding_config"]:
            try:
                branding = json.loads(r["branding_config"])
            except Exception as exc:
                import logging
                logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

        mentor_name = r["mentor_full_name"] or branding.get("mentor_name") or "Bosh Mentor"
        course_title = r["course_title"] or branding.get("course_title") or r["cabinet_name"] or "Kurs"
        mentor_id_val = f"mentor-{r['mentor_user_id']}" if r["mentor_user_id"] else "mentor-1"

        watched = r["lessons_watched"] or 0
        progress_pct = min(100, max(round(r["avg_completion"]), watched * 20))
        
        status_val = "active"
        if progress_pct >= 90 or watched >= 5:
            status_val = "graduated"
        elif watched == 0:
            status_val = "inactive"

        last_act = "Bugun faol"
        if r["last_activity_time"]:
            last_act = r["last_activity_time"][:16]
        elif r["joined_at"]:
            last_act = r["joined_at"][:10]

        results.append(
            {
                "user_id": f"st-{r['user_id']}",
                "full_name": r["full_name"] or f"Talaba #{r['user_id']}",
                "telegram_id": r["telegram_id"],
                "username": f"@id{r['telegram_id']}",
                "lessons_watched": watched,
                "last_activity": last_act,
                "progress_percent": progress_pct,
                "cabinet_id": f"cab-{r['cabinet_id']}",
                "cabinet_name": r["cabinet_name"],
                "mentor_id": mentor_id_val,
                "mentor_name": mentor_name,
                "course_title": course_title,
                "status": status_val,
            }
        )

    return results
