"""
Admin handlers uchun umumiy DB helper funksiyalar.
broadcast.py va quota.py tomonidan ishlatiladi.
"""
from __future__ import annotations

import logging

from db.database import database

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# BROADCAST uchun helperlar
# ─────────────────────────────────────────────

async def get_courses_and_counts() -> tuple[list[dict], dict[str, int]]:
    conn = database.conn
    cursor = await conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
    courses = [dict(r) for r in await cursor.fetchall()]

    counts: dict[str, int] = {}

    c_all = await conn.execute(
        "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE status = 'active' AND telegram_id IS NOT NULL"
    )
    r_all = await c_all.fetchone()
    counts["all"] = r_all["cnt"] if r_all else 0

    c_men = await conn.execute(
        "SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE role = 'mentor' AND status = 'active' AND telegram_id IS NOT NULL"
    )
    r_men = await c_men.fetchone()
    counts["mentors"] = r_men["cnt"] if r_men else 0

    for c in courses:
        cid = c["id"]
        c_crs = await conn.execute(
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

        c_std = await conn.execute(
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


async def get_mentors_list() -> list[dict]:
    """Barcha aktiv mentorlar ro'yxati (broadcast va quota uchun umumiy)."""
    conn = database.conn
    cursor = await conn.execute(
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


async def get_mentor_courses_and_counts(mentor_id: int) -> tuple[dict, list[dict], dict[str, int]]:
    conn = database.conn
    cursor_m = await conn.execute(
        "SELECT id, full_name, telegram_id FROM users WHERE id = ?", (mentor_id,)
    )
    mentor_row = await cursor_m.fetchone()
    mentor_info = dict(mentor_row) if mentor_row else {"id": mentor_id, "full_name": f"Mentor #{mentor_id}"}

    cursor_c = await conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
    courses = [dict(r) for r in await cursor_c.fetchall()]

    counts: dict[str, int] = {}

    c_all = await conn.execute(
        """
        SELECT COUNT(DISTINCT u.telegram_id) as cnt
        FROM users u
        WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
            u.id IN (
                SELECT ag.user_id FROM access_grants ag
                JOIN license_nodes ln ON ln.id = ag.node_id
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

    for c in courses:
        cid = c["id"]
        c_crs = await conn.execute(
            """
            SELECT COUNT(DISTINCT u.telegram_id) as cnt
            FROM users u
            WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                u.id IN (
                    SELECT ag.user_id FROM access_grants ag
                    JOIN license_nodes ln ON ln.id = ag.node_id
                    WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                )
                OR u.id IN (
                    SELECT cm.user_id FROM cabinet_members cm
                    JOIN cabinets c ON c.id = cm.cabinet_id
                    JOIN license_nodes ln ON ln.id = c.owner_node_id
                    JOIN access_grants ag ON ag.user_id = cm.user_id AND ag.node_id = ln.id
                    WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                )
            )
            """,
            (mentor_id, cid, mentor_id, cid),
        )
        r_crs = await c_crs.fetchone()
        counts[f"mentor_course_{cid}"] = r_crs["cnt"] if r_crs else 0

    return mentor_info, courses, counts


async def get_target_user_ids(target: str) -> list[int]:
    conn = database.conn

    if target == "all":
        cursor = await conn.execute(
            "SELECT DISTINCT telegram_id FROM users WHERE status = 'active' AND telegram_id IS NOT NULL"
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    elif target == "mentors":
        cursor = await conn.execute(
            "SELECT DISTINCT telegram_id FROM users WHERE role = 'mentor' AND status = 'active' AND telegram_id IS NOT NULL"
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]

    elif target.startswith("mentor_direct_"):
        try:
            mid = int(target.replace("mentor_direct_", ""))
            cursor = await conn.execute(
                "SELECT telegram_id FROM users WHERE id = ? AND status = 'active' AND telegram_id IS NOT NULL",
                (mid,),
            )
            row = await cursor.fetchone()
            return [row["telegram_id"]] if row and row["telegram_id"] else []
        except Exception as e:
            logger.error("Target user ids (mentor direct) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("mentor_") and "_course_" in target:
        try:
            parts = target.split("_")
            mentor_id = int(parts[1])
            cid = int(parts[3])
            cursor = await conn.execute(
                """
                SELECT DISTINCT u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                    u.id IN (
                        SELECT ag.user_id FROM access_grants ag
                        JOIN license_nodes ln ON ln.id = ag.node_id
                        WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                    )
                    OR u.id IN (
                        SELECT cm.user_id FROM cabinet_members cm
                        JOIN cabinets c ON c.id = cm.cabinet_id
                        JOIN license_nodes ln ON ln.id = c.owner_node_id
                        JOIN access_grants ag ON ag.user_id = cm.user_id AND ag.node_id = ln.id
                        WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                    )
                )
                """,
                (mentor_id, cid, mentor_id, cid),
            )
            rows = await cursor.fetchall()
            return [r["telegram_id"] for r in rows if r["telegram_id"]]
        except Exception as e:
            logger.error("Target user ids (mentor+course) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("mentor_"):
        try:
            mentor_id = int(target.replace("mentor_", ""))
            cursor = await conn.execute(
                """
                SELECT DISTINCT u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                    u.id IN (
                        SELECT ag.user_id FROM access_grants ag
                        JOIN license_nodes ln ON ln.id = ag.node_id
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
        except Exception as e:
            logger.error("Target user ids (mentor all) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("course_students_"):
        try:
            cid = int(target.replace("course_students_", ""))
            cursor = await conn.execute(
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
                (cid, cid),
            )
            rows = await cursor.fetchall()
            return [r["telegram_id"] for r in rows if r["telegram_id"]]
        except Exception as e:
            logger.error("Target user ids (course students) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("course_all_") or target.startswith("course_"):
        try:
            raw = target.replace("course_all_", "").replace("course_", "")
            cid = int(raw)
            cursor = await conn.execute(
                """
                SELECT DISTINCT u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND u.id IN (
                    SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                    UNION
                    SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
                )
                """,
                (cid, cid),
            )
            rows = await cursor.fetchall()
            return [r["telegram_id"] for r in rows if r["telegram_id"]]
        except Exception as e:
            logger.error("Target user ids olishda xato (%s): %s", target, e)
            return []

    return []


# ─────────────────────────────────────────────
# QUOTA uchun helperlar
# ─────────────────────────────────────────────

async def get_quota_mentors_list() -> list[dict]:
    """Quota boshqaruvi uchun mentorlar ro'yxati (node_id bilan)."""
    conn = database.conn
    cursor = await conn.execute(
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
