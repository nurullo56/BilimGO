from __future__ import annotations

import json
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

    @classmethod
    def create_default(cls, conn=None) -> "CabinetService":
        """Yagona markazlashgan CabinetService fabrikasi."""
        from db.database import database
        from db.repositories.cabinet_repo import CabinetRepository
        from db.repositories.chat_repo import ChatRepository
        from db.repositories.license_node_repo import LicenseNodeRepository
        from db.repositories.user_repo import UserRepository

        c = conn or database.conn
        return cls(
            cabinet_repo=CabinetRepository(c),
            chat_repo=ChatRepository(c),
            license_node_repo=LicenseNodeRepository(c),
            user_repo=UserRepository(c),
        )

    async def get_or_create_mentor_node_and_cabinet(
        self, mentor_user_id: int, course_id: int = 1
    ) -> tuple[int, str]:
        """
        Mentor uchun litsenziya tuguni va o'quv kabinetini topadi yoki yaratadi.
        Barcha SQL va repo operatsiyalari shu yerda inkapsulyatsiya qilinadi.
        """
        node = await self._license_node_repo.get_by_owner_id(mentor_user_id)
        if node:
            assigned_node_id = node.id
        else:
            assigned_node_id = await self._license_node_repo.create_node(
                owner_user_id=mentor_user_id,
                course_id=course_id,
                parent_id=1,
                royalty_percent=20.0,
                stage="limit",
                status="active",
                autocommit=True,
            )

        cabinet = await self.get_or_create_for_node(assigned_node_id)
        return assigned_node_id, cabinet.display_name

    async def get_mentor_students(self, mentor_user_id: int) -> list[dict]:
        """Mentorning barcha kabinetlaridagi talabalar ro'yxatini oladi."""
        cabinet_ids = await self._cabinet_repo.get_owned_cabinet_ids(mentor_user_id)
        students: list[dict] = []
        for cid in cabinet_ids:
            st = await self._cabinet_repo.list_students(cid)
            students.extend(st)
        return students

    async def has_owned_cabinets(self, mentor_user_id: int) -> bool:
        """Mentorga tegishli kamida 1 ta kabinet bor yoki yo'qligini tekshiradi."""
        cabinet_ids = await self._cabinet_repo.get_owned_cabinet_ids(mentor_user_id)
        return len(cabinet_ids) > 0

    async def list_user_cabinets(self, user_id: int) -> list[dict]:
        """Foydalanuvchi a'zo bo'lgan barcha kabinet va guruh chatlarini qaytaradi."""
        return await self._cabinet_repo.list_my_cabinets(user_id)

    async def get_user_cabinets(self, user_id: int, is_admin: bool) -> list[dict]:
        """Foydalanuvchiga tegishli kabinetlar ro'yxatini to'liq brending va ma'lumotlar bilan qaytaradi."""
        rows = await self._cabinet_repo.get_user_cabinets_with_details(user_id, is_admin)
        results = []
        for r in rows:
            branding = {}
            if r.get("branding_config"):
                try:
                    branding = json.loads(r["branding_config"])
                except Exception:
                    branding = {}

            results.append(
                {
                    "id": f"cab-{r['id']}",
                    "display_name": r["display_name"],
                    "role_in_cabinet": r.get("role_in_cabinet") or "student",
                    "avatar": branding.get("avatar") or "💬",
                    "unread_count": 0,
                    "course_id": branding.get("course_id"),
                    "course_title": branding.get("course_title"),
                    "description": branding.get("description"),
                    "mentor_name": branding.get("mentor_name") or "Mentor",
                    "students_count": max(1, r.get("students_count") or 1),
                    "created_at": r.get("created_at"),
                }
            )
        return results

    async def create_cabinet_flow(
        self,
        creator_user_id: int,
        display_name: str,
        avatar: str | None = "💬",
        description: str | None = None,
        course_id: int | str | None = None,
        course_title: str | None = None,
        initial_message: str | None = None,
    ) -> dict:
        """Yangi kabinet yaratish, mentorni qo'shish, chat xonasi va boshlang'ich xabarni yozish."""
        user = await self._user_repo.get_by_id(creator_user_id)
        mentor_name = user.full_name if (user and user.full_name) else "Mentor"

        node = await self._license_node_repo.get_by_owner_id(creator_user_id)
        node_id = node.id if node else 1

        course_id_clean = None
        if course_id:
            try:
                course_id_clean = int(str(course_id).replace("course-", ""))
            except ValueError:
                course_id_clean = 1

        branding = {
            "avatar": avatar or "💬",
            "description": description,
            "course_id": course_id,
            "course_title": course_title,
            "mentor_name": mentor_name,
        }
        branding_str = json.dumps(branding, ensure_ascii=False)

        cab_row = await self._cabinet_repo.create_cabinet_record(
            owner_node_id=node_id,
            display_name=display_name.strip(),
            branding_config=branding_str,
        )
        cab_id = cab_row["id"]

        # Add creator as mentor in cabinet_members
        await self._cabinet_repo.add_member(cab_id, creator_user_id, role="mentor")

        # Create default room & add user to chat_room_members
        room_id = await self._chat_repo.create_room(cab_id, course_id_clean or 1)
        await self._chat_repo.add_room_member(room_id, creator_user_id)

        # If initial message provided, send it
        if initial_message and initial_message.strip():
            await self._chat_repo.send_message(
                room_id=room_id,
                sender_id=creator_user_id,
                content=initial_message.strip(),
            )

        return {
            "id": f"cab-{cab_id}",
            "display_name": display_name.strip(),
            "role_in_cabinet": "mentor",
            "avatar": avatar or "💬",
            "unread_count": 0,
            "course_id": course_id,
            "course_title": course_title,
            "description": description,
            "created_at": cab_row.get("created_at") or "2026-01-01",
            "mentor_name": mentor_name,
            "students_count": 1,
        }

    async def update_cabinet_branding(
        self,
        cabinet_id: int,
        display_name: str,
        avatar: str | None = None,
        description: str | None = None,
        course_title: str | None = None,
    ) -> dict:
        """Kabinet ma'lumotlari va brendingini yangilaydi."""
        raw_branding = await self._cabinet_repo.get_branding_config(cabinet_id)
        current_branding = {}
        if raw_branding:
            try:
                current_branding = json.loads(raw_branding)
            except Exception:
                current_branding = {}

        if avatar:
            current_branding["avatar"] = avatar
        if description is not None:
            current_branding["description"] = description
        if course_title:
            current_branding["course_title"] = course_title

        branding_str = json.dumps(current_branding, ensure_ascii=False)
        await self._cabinet_repo.update_cabinet_branding(
            cabinet_id=cabinet_id,
            display_name=display_name.strip(),
            branding_config=branding_str,
        )

        return {
            "id": f"cab-{cabinet_id}",
            "display_name": display_name.strip(),
            "avatar": current_branding.get("avatar") or "💬",
            "description": current_branding.get("description"),
            "course_title": current_branding.get("course_title"),
            "role_in_cabinet": "mentor",
            "students_count": 1,
            "unread_count": 0,
        }

    async def delete_cabinet(self, cabinet_id: int) -> None:
        """Kabinetni kaskadli o'chiradi."""
        await self._cabinet_repo.delete_cascade(cabinet_id)



