from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.student_kb import get_checkout_payment_keyboard

from core.config import settings
from core.exceptions import NotFoundError
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.royalty_repo import RoyaltyLedgerRepository
from db.repositories.sale_repo import SaleRepository
from db.repositories.user_repo import User, UserRepository
from services.cabinet_service import CabinetService
from services.payment_service import PaymentService
from services.royalty_service import RoyaltyService

router = Router(name="student_purchase")


def _build_payment_service() -> PaymentService:
    conn = database.conn
    royalty_service = RoyaltyService(LicenseNodeRepository(conn), RoyaltyLedgerRepository(conn))
    user_repo = UserRepository(conn)
    cabinet_service = CabinetService(
        cabinet_repo=CabinetRepository(conn),
        chat_repo=ChatRepository(conn),
        license_node_repo=LicenseNodeRepository(conn),
        user_repo=user_repo,
    )
    return PaymentService(
        course_repo=CourseRepository(conn),
        sale_repo=SaleRepository(conn),
        access_grant_repo=AccessGrantRepository(conn),
        royalty_service=royalty_service,
        cabinet_service=cabinet_service,
        user_repo=user_repo,
    )


@router.callback_query(F.data.startswith("buy:"))
async def handle_buy(callback: CallbackQuery, user: User) -> None:
    _, course_id_raw, provider = callback.data.split(":")
    course_id = int(course_id_raw)

    course_repo = CourseRepository(database.conn)
    course = await course_repo.get_by_id(course_id)
    if course is None or course.owner_node_id is None:
        await callback.answer("Kurs sotuvda emas", show_alert=True)
        return

    payment_service = _build_payment_service()
    try:
        pending = await payment_service.initiate_purchase(
            student_id=user.id,
            course_id=course_id,
            license_node_id=course.owner_node_id,
            provider=provider,
        )
    except NotFoundError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    if provider == "click":
        url = settings.click.build_checkout_url(
            sale_id=pending.sale_id, amount=pending.amount,
            return_url=settings.webapp.course_url(course_id),
        )
    else:
        url = settings.payme.build_checkout_url(sale_id=pending.sale_id, amount=pending.amount)

    keyboard = get_checkout_payment_keyboard(provider=provider, checkout_url=url)
    await callback.message.answer(
        f"To'lov summasi: {pending.amount:,.0f} so'm\n\nTo'lovni yakunlash uchun tugmani bosing:",
        reply_markup=keyboard,
    )
    await callback.answer()
