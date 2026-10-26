from __future__ import annotations
import logging
from typing import Any, Optional
from db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repo: Optional[UserRepository] = None) -> None:
        self.user_repo = user_repo or UserRepository()

    async def get_user_profile(self, user_id: int) -> Optional[dict[str, Any]]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return dict(user)

    async def update_user_status(self, user_id: int, status: str) -> None:
        await self.user_repo.update_status(user_id, status)
