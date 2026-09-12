from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from db.database import database
from db.repositories.server_expense_repo import ServerExpenseRepository
from db.repositories.user_repo import UserRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/server-expenses", tags=["server_expenses"])


@router.get("/mentor-summary")
async def get_mentor_server_expenses_summary(
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """Mentor uchun shogirdlarining server, video trafigi va hosting xarajatlari hisoboti."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    repo = ServerExpenseRepository(conn)

    summary = await repo.get_mentor_summary(user.id)
    recent = await repo.list_mentor_recent(user.id, limit=15)

    return {
        "summary": summary,
        "recent_expenses": recent,
    }
