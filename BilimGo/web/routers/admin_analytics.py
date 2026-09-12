from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Query

from db.database import database
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.user_repo import UserRepository
from services.analytics_service import AnalyticsService
from web.dependencies.auth import get_current_telegram_id

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


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
        COUNT(DISTINCT lv.id) AS lessons_watched,
        COALESCE(MAX(lv.completion_percent), 0) AS max_completion,
        COALESCE(AVG(lv.completion_percent), 0) AS avg_completion,
        MAX(lv.started_at) AS last_activity_time
    FROM cabinet_members cm
    JOIN users u ON u.id = cm.user_id
    JOIN cabinets c ON c.id = cm.cabinet_id
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

        mentor_name = branding.get("mentor_name") or "Nurulloh (Bosh Mentor)"
        course_title = branding.get("course_title") or "Python & Backend Muhandisligi"

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
                "mentor_id": "mentor-1",
                "mentor_name": mentor_name,
                "course_title": course_title,
                "status": status_val,
            }
        )

    return results
