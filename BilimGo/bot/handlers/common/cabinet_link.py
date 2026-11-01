from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.common import get_cabinets_keyboard
from db.repositories.user_repo import User
from services.cabinet_service import CabinetService

router = Router(name="cabinet_link")


@router.message(F.text.in_(["💬 Kabinet va chat", "💬 Guruh chati", "💬 Barcha Chatlar"]))
async def show_cabinets(message: Message, user: User) -> None:
    cabinet_service = CabinetService.create_default()
    cabinets = await cabinet_service.list_user_cabinets(user.id)
    keyboard = get_cabinets_keyboard(cabinets)

    if not cabinets:
        await message.answer(
            "Sizda hali biriktirilgan maxsus guruh chatlari yo'q.\n"
            "Umumiy kabinetni ochish uchun quyidagi tugmani bosing:",
            reply_markup=keyboard,
        )
        return

    await message.answer("👥 <b>Siz a'zo bo'lgan kabinet va guruh chatlari:</b>", reply_markup=keyboard)
