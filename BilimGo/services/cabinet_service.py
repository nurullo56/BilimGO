from __future__ import annotations

from db.repositories.cabinet_repo import Cabinet, CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import UserRepository


class CabinetService:
    def __init__(
        self,
        cabinet_repo: CabinetRepository,
        chat_repo: ChatRepository,
        license_node_repo: LicenseNodeRepository,
        user_repo: UserRepository,
    ) -> None:
        self._cabinet_repo = cabinet_repo
        self._chat_repo = chat_repo
        self._license_node_repo = license_node_repo
        self._user_repo = user_repo

    async def get_or_create_for_node(self, license_node_id: int) -> Cabinet:
        existing = await self._cabinet_repo.get_by_owner_node(license_node_id)
        if existing is not None:
            return existing

        node = await self._license_node_repo.get_by_id(license_node_id)
        assert node is not None
        owner = await self._user_repo.get_by_id(node.owner_user_id)
        display_name = f"{owner.full_name}'s kabineti" if owner else f"Kabinet #{license_node_id}"

        cabinet = await self._cabinet_repo.create(license_node_id, display_name)
        await self._cabinet_repo.add_member(cabinet.id, node.owner_user_id, role="mentor")
        return cabinet

    async def enroll_student_after_purchase(
        self, license_node_id: int, student_id: int, course_id: int
    ) -> None:
        """Talaba kursni sotib olganda chaqiriladi: mentorning kabinetiga
        va shu kurs uchun chat xonasiga avtomatik qo'shadi."""
        cabinet = await self.get_or_create_for_node(license_node_id)
        await self._cabinet_repo.add_member(cabinet.id, student_id, role="student")

        room_id = await self._chat_repo.create_room(cabinet.id, course_id)
        await self._chat_repo.add_room_member(room_id, student_id)

        node = await self._license_node_repo.get_by_id(license_node_id)
        assert node is not None
        await self._chat_repo.add_room_member(room_id, node.owner_user_id)
