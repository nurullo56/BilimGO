import logging
from dataclasses import dataclass
from typing import Literal

from core.exceptions import NotFoundError
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.sale_repo import SaleRepository
from db.repositories.user_repo import UserRepository
from services.auto_debit_service import AutoDebitService
from services.cabinet_service import CabinetService
from services.royalty_service import RoyaltyService
from services.userbot_client import UserbotClient

logger = logging.getLogger(__name__)

PaymentProvider = Literal["click", "payme"]


@dataclass(slots=True)
class PendingPurchase:
    sale_id: int
    amount: float


class PaymentService:
    def __init__(
        self,
        course_repo: CourseRepository,
        sale_repo: SaleRepository,
        access_grant_repo: AccessGrantRepository,
        royalty_service: RoyaltyService,
        cabinet_service: CabinetService,
        user_repo: UserRepository | None = None,
        userbot_client: UserbotClient | None = None,
        auto_debit_service: AutoDebitService | None = None,
    ) -> None:
        self._course_repo = course_repo
        self._sale_repo = sale_repo
        self._access_grant_repo = access_grant_repo
        self._royalty_service = royalty_service
        self._cabinet_service = cabinet_service
        self._user_repo = user_repo
        self._userbot_client = userbot_client or UserbotClient()
        self._auto_debit_service = auto_debit_service

    async def initiate_purchase(
        self,
        student_id: int,
        course_id: int,
        license_node_id: int,
        provider: PaymentProvider,
    ) -> PendingPurchase:
        course = await self._course_repo.get_by_id(course_id)
        if course is None or course.status != "published":
            raise NotFoundError(f"Kurs mavjud emas yoki nashr qilinmagan: id={course_id}")

        effective_node_id = license_node_id
        if license_node_id > 1:
            node = await self._royalty_service._license_node_repo.get_by_id(license_node_id)
            if node and node.status in ("suspended", "terminated"):
                logger.warning(
                    "License node #%s to'xtatilgan (status=%s). Xarid bosh node #1 ga yo'naltirilmoqda.",
                    license_node_id,
                    node.status,
                )
                effective_node_id = 1

        sale_id = await self._sale_repo.create_pending(
            student_id=student_id,
            course_id=course_id,
            license_node_id=effective_node_id,
            amount=course.base_price,
            payment_provider=provider,
        )
        return PendingPurchase(sale_id=sale_id, amount=course.base_price)

    async def confirm_payment(self, sale_id: int, external_txn_id: str) -> None:
        """To'lov provayderi (Click/Payme) tomonidan tasdiqlangandan keyin
        chaqiriladi: sale'ni 'paid' qiladi, kursga kirish huquqini beradi
        va royalty'ni daraxt bo'ylab taqsimlaydi. Idempotent."""
        sale = await self._sale_repo.get_by_id(sale_id)
        if sale is None:
            raise NotFoundError(f"Sale topilmadi: id={sale_id}")

        if sale.payment_status == "paid":
            return  # allaqachon ishlov berilgan — qayta bajarilmaydi

        await self._sale_repo.mark_paid(sale_id, external_txn_id)

        sale = await self._sale_repo.get_by_id(sale_id)
        assert sale is not None

        await self._access_grant_repo.grant_course_access(
            user_id=sale.student_id,
            course_id=sale.course_id,
            granted_via_sale_id=sale.id,
        )
        await self._royalty_service.distribute_for_sale(sale)
        await self._cabinet_service.enroll_student_after_purchase(
            license_node_id=sale.license_node_id,
            student_id=sale.student_id,
            course_id=sale.course_id,
        )

        if self._auto_debit_service:
            try:
                # Har 10 ta o'quvchi xarid qilganda mentor kartasidan royaltini avtomatik yechish
                await self._auto_debit_service.check_and_auto_debit_royalty(
                    child_node_id=sale.license_node_id, threshold_students=10
                )
            except Exception:
                logger.exception("Avto-debit tekshirishda xatolik, sale_id=%s", sale.id)

        if self._user_repo:
            try:
                student = await self._user_repo.get_by_id(sale.student_id)
                course = await self._course_repo.get_by_id(sale.course_id)
                if student and course:
                    success_text = (
                        f"🎉 <b>To'lov muvaffaqiyatli qabul qilindi!</b>\n\n"
                        f"📚 Kurs: <b>«{course.title}»</b>\n"
                        f"💰 To'langan summa: <b>{sale.amount:,.0f} so'm</b>\n\n"
                        f"Kurs siz uchun ochildi! «🎓 Mening kurslarim» bo'limi orqali darslarni boshlashingiz mumkin. Omad! 🚀"
                    )
                    await self._userbot_client.send_message(student.telegram_id, success_text)
            except Exception:
                logger.exception("To'lov tasdiqlangach bildirishnoma yuborishda xato, sale_id=%s", sale.id)
