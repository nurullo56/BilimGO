from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.student import get_checkout_payment_keyboard
from core.config import settings
from core.exceptions import NotFoundError
from db.repositories.user_repo import User
from services.course_service import CourseService
from services.payment_service import PaymentService

router = Router(name="student_purchase")


@router.callback_query(F.data.startswith("buy:"))
async def handle_buy(callback: CallbackQuery, user: User) -> None:
    _, course_id_raw, provider = callback.data.split(":")
    course_id = int(course_id_raw)

    course_service = CourseService()
    course = await course_service.get_by_id(course_id)
    if course is None or course.owner_node_id is None:
        await callback.answer("Kurs sotuvda emas", show_alert=True)
        return

    payment_service = PaymentService.create_default()
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
            sale_id=pending.sale_id,
            amount=pending.amount,
            return_url=settings.webapp.course_url(course_id),
        )
    else:
        url = settings.payme.build_checkout_url(sale_id=pending.sale_id, amount=pending.amount)

    keyboard = get_checkout_payment_keyboard(provider=provider, checkout_url=url)
    is_konkurs = course_id == 3 or (course and ("konkurs" in course.title.lower() or "aksiya" in course.title.lower()))
    konkurs_warning = ""
    if is_konkurs:
        konkurs_warning = (
            "⚠️ <b>DIQQAT:</b> Konkurs boti va barcha imtiyozlar faqat hozir to'lov qilayotgan ushbu Telegram akkauntingizga biriktiriladi. "
            "Boshqa akkauntga o'tkazib berilmaydi!\n\n"
        )
    await callback.message.answer(
        f"{konkurs_warning}To'lov summasi: {pending.amount:,.0f} so'm\n\nTo'lovni yakunlash uchun tugmani bosing:",
        reply_markup=keyboard,
    )
    await callback.answer()
