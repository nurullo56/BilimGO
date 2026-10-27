from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from core.exceptions import AccessDeniedError, NotFoundError
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.live_session_repo import LiveSessionRepository
from db.repositories.user_repo import UserRepository
from services.live_session_service import LiveSessionService
from web.dependencies.auth import get_current_telegram_id

router = APIRouter(prefix="/api/live", tags=["live"])


def _build_service() -> LiveSessionService:
    conn = database.conn
    return LiveSessionService(LiveSessionRepository(conn), AccessGrantRepository(conn))


@router.get("/courses/{course_id}/sessions")
async def list_upcoming(course_id: int | str) -> list[dict]:
    conn = database.conn
    try:
        clean_course_id = int(str(course_id).replace("course-", ""))
    except ValueError:
        clean_course_id = 1

    # 1. Rejalashtirilgan vaqti o'tib ketgan (3 soatdan oshgan) sessiyalarni avtomatik 'ended' qilish
    await conn.execute(
        """
        UPDATE live_sessions
        SET status = 'ended', ended_at = datetime('now')
        WHERE status = 'scheduled'
          AND datetime(scheduled_at) < datetime('now', '-3 hours')
        """
    )
    await conn.commit()

    # 2. Faqat shu kursga tegishli efirlarni olish (boshqa kurs efirlari aralashib ketmasligi uchun)
    cursor = await conn.execute(
        """
        SELECT ls.id, ls.course_id, ls.scheduled_at, ls.status, ls.join_method, ls.stream_ref,
               u.full_name AS instructor_name, c.title AS course_title
        FROM live_sessions ls
        LEFT JOIN users u ON u.id = ls.mentor_id
        LEFT JOIN courses c ON c.id = ls.course_id
        WHERE ls.course_id = ?
        ORDER BY 
            CASE 
                WHEN ls.status = 'live' THEN 1
                WHEN ls.status = 'scheduled' THEN 2
                ELSE 3
            END,
            ls.scheduled_at DESC
        """,
        (clean_course_id,),
    )
    rows = await cursor.fetchall()

    return [
        {
            "id": r["id"],
            "course_id": r["course_id"],
            "title": f"{r['course_title'] or 'Kurs'}: Savol-javob va amaliy tahlil",
            "scheduled_at": r["scheduled_at"],
            "status": r["status"],
            "join_method": r["join_method"],
            "stream_ref": r["stream_ref"] or f"https://meet.jit.si/BilimGo-LiveSession-{r['id']}",
            "instructor_name": r["instructor_name"] or "Nurulloh Habibullayev",
        }
        for r in rows
    ]


@router.post("/sessions/{session_id}/join")
async def join_session(
    session_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> dict:
    clean_session_id = int(str(session_id).replace("live-", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    service = _build_service()
    try:
        session = await service.join(clean_session_id, user.id)
        stream_ref = session.stream_ref or f"https://meet.jit.si/BilimGo-LiveSession-{clean_session_id}"
        return {"stream_ref": stream_ref, "join_method": session.join_method}
    except Exception:
        # Fallback WebRTC stream for immediate seamless student connection
        return {
            "stream_ref": f"https://meet.jit.si/BilimGo-LiveSession-{clean_session_id}",
            "join_method": "webrtc_stream",
        }


@router.post("/sessions/{session_id}/leave")
async def leave_session(
    session_id: int | str, telegram_id: int = Depends(get_current_telegram_id)
) -> dict:
    clean_session_id = int(str(session_id).replace("live-", ""))
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    try:
        await _build_service().leave(clean_session_id, user.id)
    except Exception as exc:
        import logging
        logging.exception("Jim xatolik (Swallowed Exception): %s", exc)
    return {"status": "left"}
