from __future__ import annotations

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.database import database
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.user_repo import UserRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cabinets", tags=["cabinets"])


class CreateCabinetPayload(BaseModel):
    display_name: str
    avatar: str | None = "💬"
    description: str | None = None
    course_id: int | str | None = None
    course_title: str | None = None
    initial_message: str | None = None


@router.get("/me")
async def my_cabinets(telegram_id: int = Depends(get_current_telegram_id)) -> list[dict]:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)

    # Return all cabinets user is a member of (or all if admin/super_mentor)
    is_admin = user.role in ("admin", "super_mentor")

    if is_admin:
        cursor = await conn.execute(
            """
            SELECT c.id, c.display_name, c.branding_config, c.created_at,
                   COALESCE(cm.role_in_cabinet, 'mentor') as role_in_cabinet,
                   (SELECT COUNT(*) FROM cabinet_members WHERE cabinet_id = c.id AND role_in_cabinet = 'student') as students_count
            FROM cabinets c
            LEFT JOIN cabinet_members cm ON cm.cabinet_id = c.id AND cm.user_id = ?
            ORDER BY c.id DESC
            """,
            (user.id,),
        )
    else:
        cursor = await conn.execute(
            """
            SELECT c.id, c.display_name, c.branding_config, c.created_at, cm.role_in_cabinet,
                   (SELECT COUNT(*) FROM cabinet_members WHERE cabinet_id = c.id AND role_in_cabinet = 'student') as students_count
            FROM cabinet_members cm
            JOIN cabinets c ON c.id = cm.cabinet_id
            WHERE cm.user_id = ?
            ORDER BY c.id DESC
            """,
            (user.id,),
        )

    rows = await cursor.fetchall()
    results = []
    for r in rows:
        branding = {}
        if r["branding_config"]:
            try:
                branding = json.loads(r["branding_config"])
            except Exception:
                branding = {}

        results.append(
            {
                "id": f"cab-{r['id']}",
                "display_name": r["display_name"],
                "role_in_cabinet": r["role_in_cabinet"] or "student",
                "avatar": branding.get("avatar") or "💬",
                "unread_count": 0,
                "course_id": branding.get("course_id"),
                "course_title": branding.get("course_title"),
                "description": branding.get("description"),
                "mentor_name": branding.get("mentor_name") or "Mentor",
                "students_count": max(1, r["students_count"] or 1),
                "created_at": r["created_at"],
            }
        )

    return results


@router.get("/{cabinet_id}/students")
async def cabinet_students(
    cabinet_id: str | int, telegram_id: int = Depends(get_current_telegram_id)
) -> list[dict]:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    cabinet_repo = CabinetRepository(conn)

    is_admin = user.role in ("admin", "super_mentor")
    is_member = await cabinet_repo.is_member(clean_id, user.id)
    if not is_member and not is_admin:
        # Check if user can be added as mentor/student
        pass

    return await cabinet_repo.list_students(clean_id)


@router.get("/{cabinet_id}/rooms")
async def cabinet_rooms(
    cabinet_id: str | int, telegram_id: int = Depends(get_current_telegram_id)
) -> list[dict]:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    chat_repo = ChatRepository(database.conn)
    return await chat_repo.list_rooms_for_cabinet(clean_id)


@router.post("")
async def create_cabinet(
    payload: CreateCabinetPayload,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)

    # Determine node_id
    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1", (user.id,)
    )
    node_row = await cursor.fetchone()
    node_id = node_row["id"] if node_row else 1

    course_id_clean = None
    if payload.course_id:
        try:
            course_id_clean = int(str(payload.course_id).replace("course-", ""))
        except ValueError:
            course_id_clean = 1

    mentor_name = user.full_name or "Mentor"
    branding = {
        "avatar": payload.avatar or "💬",
        "description": payload.description,
        "course_id": payload.course_id,
        "course_title": payload.course_title,
        "mentor_name": mentor_name,
    }
    branding_str = json.dumps(branding, ensure_ascii=False)

    cursor = await conn.execute(
        """
        INSERT INTO cabinets (owner_node_id, display_name, branding_config)
        VALUES (?, ?, ?)
        RETURNING id, display_name, created_at
        """,
        (node_id, payload.display_name.strip(), branding_str),
    )
    cab_row = await cursor.fetchone()
    cab_id = cab_row["id"]
    await conn.commit()

    # Add creator as mentor in cabinet_members
    await cabinet_repo.add_member(cab_id, user.id, role="mentor")

    # Create default room & add user to chat_room_members
    room_id = await chat_repo.create_room(cab_id, course_id_clean or 1)
    await chat_repo.add_room_member(room_id, user.id)

    # If initial message provided, send it
    if payload.initial_message:
        await conn.execute(
            """
            INSERT INTO chat_messages (room_id, sender_id, content)
            VALUES (?, ?, ?)
            """,
            (room_id, user.id, payload.initial_message.strip()),
        )
        await conn.commit()

    return {
        "id": f"cab-{cab_id}",
        "display_name": payload.display_name.strip(),
        "role_in_cabinet": "mentor",
        "avatar": payload.avatar or "💬",
        "unread_count": 0,
        "course_id": payload.course_id,
        "course_title": payload.course_title,
        "description": payload.description,
        "created_at": cab_row["created_at"] if "created_at" in cab_row.keys() else "2026-01-01",
        "mentor_name": mentor_name,
        "students_count": 1,
    }


@router.put("/{cabinet_id}")
async def update_cabinet(
    cabinet_id: str | int,
    payload: CreateCabinetPayload,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)

    # Get current branding
    cursor = await conn.execute("SELECT branding_config FROM cabinets WHERE id = ?", (clean_id,))
    row = await cursor.fetchone()
    current_branding = {}
    if row and row["branding_config"]:
        try:
            current_branding = json.loads(row["branding_config"])
        except Exception as exc:
            import logging
            logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    if payload.avatar:
        current_branding["avatar"] = payload.avatar
    if payload.description is not None:
        current_branding["description"] = payload.description
    if payload.course_title:
        current_branding["course_title"] = payload.course_title

    await conn.execute(
        "UPDATE cabinets SET display_name = ?, branding_config = ? WHERE id = ?",
        (payload.display_name.strip(), json.dumps(current_branding, ensure_ascii=False), clean_id),
    )
    await conn.commit()

    return {
        "id": f"cab-{clean_id}",
        "display_name": payload.display_name.strip(),
        "avatar": current_branding.get("avatar") or "💬",
        "description": current_branding.get("description"),
        "course_title": current_branding.get("course_title"),
        "role_in_cabinet": "mentor",
        "students_count": 1,
        "unread_count": 0,
    }


@router.delete("/{cabinet_id}")
async def delete_cabinet(
    cabinet_id: str | int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    clean_id = int(str(cabinet_id).replace("cab-", ""))
    conn = database.conn

    await conn.execute("DELETE FROM chat_messages WHERE room_id IN (SELECT id FROM chat_rooms WHERE cabinet_id = ?)", (clean_id,))
    await conn.execute("DELETE FROM chat_room_members WHERE room_id IN (SELECT id FROM chat_rooms WHERE cabinet_id = ?)", (clean_id,))
    await conn.execute("DELETE FROM chat_rooms WHERE cabinet_id = ?", (clean_id,))
    await conn.execute("DELETE FROM cabinet_members WHERE cabinet_id = ?", (clean_id,))
    await conn.execute("DELETE FROM cabinets WHERE id = ?", (clean_id,))
    await conn.commit()
    return {"success": True}
