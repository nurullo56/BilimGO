from __future__ import annotations

import html
import logging
import uuid
import httpx

from core.config import settings
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.mentor_card_repo import MentorCardRepository
from db.repositories.royalty_repo import RoyaltyLedgerRepository
from db.repositories.user_repo import UserRepository
from services.userbot_client import UserbotClient

logger = logging.getLogger(__name__)


class AutoDebitService:
    """Payme / Click Subscribe API orqali mentordan royalti komissiyasini avtomatik yechib olish servisi."""

    def __init__(
        self,
        node_repo: LicenseNodeRepository,
        royalty_repo: RoyaltyLedgerRepository,
        card_repo: MentorCardRepository,
        user_repo: UserRepository,
        userbot_client: UserbotClient | None = None,
    ) -> None:
        self._node_repo = node_repo
        self._royalty_repo = royalty_repo
        self._card_repo = card_repo
        self._user_repo = user_repo
        self._userbot_client = userbot_client or UserbotClient()

    async def charge_card(
        self, provider: str, card_token: str, amount_sum: float, description: str
    ) -> tuple[bool, str]:
        """Payme yoki Click Subscribe API orqali kartadan to'lov yechish."""
        if (
            settings.debug
            or card_token.startswith("mock_")
            or card_token.startswith("payme_token_")
            or not settings.payme.secret_key
        ):
            # Lokal test/debug rejimida muvaffaqiyatli deb hisoblash
            mock_txn_id = f"auto_txn_{uuid.uuid4().hex[:10]}"
            logger.info("Mock auto-debit (%s): token=%s, amount=%s sum", provider, card_token[:8], amount_sum)
            return True, mock_txn_id

        # Production Payme / Click Subscribe API chaqiruvlari
        if provider == "payme":
            return await self._charge_payme(card_token, amount_sum, description)
        else:
            return await self._charge_click(card_token, amount_sum, description)

    async def _charge_payme(self, card_token: str, amount_sum: float, description: str) -> tuple[bool, str]:
        amount_tiyin = int(amount_sum * 100)
        # Payme Subscribe API: receipts.create -> receipts.pay
        headers = {"X-Auth": f"{settings.payme.merchant_id}:{settings.payme.secret_key}"}
        url = "https://checkout.paycom.uz/api"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. receipts.create
                create_payload = {
                    "method": "receipts.create",
                    "params": {
                        "amount": amount_tiyin,
                        "account": {"description": description},
                    },
                }
                resp1 = await client.post(url, json=create_payload, headers=headers)
                data1 = resp1.json()
                if "error" in data1 or not data1.get("result"):
                    return False, str(data1.get("error"))

                receipt_id = data1["result"]["receipt"]["_id"]

                # 2. receipts.pay
                pay_payload = {
                    "method": "receipts.pay",
                    "params": {"id": receipt_id, "token": card_token},
                }
                resp2 = await client.post(url, json=pay_payload, headers=headers)
                data2 = resp2.json()
                if "error" in data2 or not data2.get("result"):
                    return False, str(data2.get("error"))

                return True, receipt_id
        except Exception as exc:
            logger.exception("Payme auto-debit xatolik")
            return False, str(exc)

    async def _charge_click(self, card_token: str, amount_sum: float, description: str) -> tuple[bool, str]:
        # Click token payment API
        url = "https://api.click.uz/v2/merchant/payment/token"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Auth": f"{settings.click.merchant_id}:{settings.click.secret_key}",
        }
        payload = {
            "service_id": settings.click.service_id,
            "card_token": card_token,
            "amount": amount_sum,
            "transaction_param": description,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                data = resp.json()
                if data.get("error_code") == 0:
                    return True, str(data.get("payment_id", "click_success"))
                return False, str(data.get("error_note", "Click to'lov xatosi"))
        except Exception as exc:
            logger.exception("Click auto-debit xatolik")
            return False, str(exc)

    async def check_and_auto_debit_royalty(
        self, child_node_id: int, threshold_students: int = 10
    ) -> dict:
        """Har bir 10 yoki 15 ta o'quvchi xarid qilganda royaltini mentordan avtomatik yechib olish."""
        node = await self._node_repo.get_by_id(child_node_id)
        if node is None:
            return {"status": "node_not_found"}

        # Limit davrida (15 kun ichida) bo'lsa, 0% haq olinadi
        if node.stage == "limit":
            return {"status": "in_limit_period", "message": "15 kunlik limit davrida royalti olinmaydi"}

        info = await self._royalty_repo.unsettled_info_for_child_node(child_node_id)
        sales_count = info["sales_count"]
        total_amount = info["total_amount"]

        if sales_count < threshold_students or total_amount <= 0:
            return {
                "status": "threshold_not_reached",
                "sales_count": sales_count,
                "total_amount": total_amount,
                "threshold": threshold_students,
            }

        mentor = await self._user_repo.get_by_id(node.owner_user_id)
        if mentor is None:
            return {"status": "mentor_not_found"}

        card = await self._card_repo.get_active_card(mentor.id)
        mentor_name = html.escape(mentor.full_name or "Mentor")

        if card is None:
            # 1. Mentor litsenziyasini to'xtatish (suspended)
            await self._node_repo.update_status(node.id, "suspended")

            # 2. Mentorga ogohlantirish yuborish
            reminder_msg = (
                f"🚨 <b>DIQQAT! QABUL VAQTINCHA TO'XTATILDI!</b>\n\n"
                f"Hurmatli <b>{mentor_name}</b>, sizning kabinetingizda <b>{sales_count} ta o'quvchi</b> o'qidi va "
                f"to'lanishi lozim bo'lgan royalti <b>{total_amount:,.0f} so'm</b>ni tashkil etmoqda.\n\n"
                f"⚠️ To'lov kartasi ulanmaganligi sababli <b>yangi o'quvchilarni qabul qilish vaqtincha to'xtatildi</b>.\n\n"
                f"Qabulni qayta ochish uchun botdagi «💳 Ulangan karta (Avto-to'lov)» bo'limi orqali kartangizni ulang."
            )
            try:
                await self._userbot_client.send_message(mentor.telegram_id, reminder_msg)
            except Exception as e:
                logger.warning("Mentorga to'xtatilish xabarini yuborishda xato: %s", e)

            # 3. Super Mentor / Adminga xabar yuborish
            admin_alert = (
                f"🚨 <b>MENTOR QABULI TO'XTATILDI (Karta ulanmagan)!</b>\n\n"
                f"👤 Mentor: <b>{mentor_name}</b> (ID: <code>{mentor.telegram_id}</code>)\n"
                f"🔑 Litsenziya: Node #{node.id}\n"
                f"👥 O'qitilgan: <b>{sales_count} ta o'quvchi</b>\n"
                f"💵 Qarz: <b>{total_amount:,.0f} so'm</b>\n\n"
                f"Mentor to'lov kartasini ulamagani sababli yangi o'quvchilarni qabul qilishi vaqtinchalik to'xtatildi (suspended)."
            )
            for admin_id in settings.bot.admin_ids:
                if admin_id != mentor.telegram_id:
                    try:
                        await self._userbot_client.send_message(admin_id, admin_alert)
                    except Exception as e:
                        logger.warning("Adminga ogohlantirish yuborishda xato: %s", e)

            return {"status": "card_not_linked", "suspended": True, "sales_count": sales_count, "amount": total_amount}

        # Kartadan avtomatik yechib olish
        desc = f"Royalty settlement node #{node.id} for {sales_count} students"
        success, txn_id = await self.charge_card(
            provider=card.provider,
            card_token=card.card_token,
            amount_sum=total_amount,
            description=desc,
        )

        if not success:
            logger.error("Royalti avto-debit xatolik node_id=%s, txn=%s", node.id, txn_id)

            # 1. Mentor litsenziyasini to'xtatish (suspended)
            await self._node_repo.update_status(node.id, "suspended")

            # 2. Xatolikni qayd etish
            await self._royalty_repo.record_auto_settlement(
                node_id=node.id,
                mentor_id=mentor.id,
                amount=total_amount,
                sales_count=sales_count,
                provider=card.provider,
                external_txn_id=str(txn_id),
                status="failed",
            )

            # 3. Mentorga xabar
            fail_msg = (
                f"🚨 <b>DIQQAT! AVTO-TO'LOV AMALGA OSHMADI — QABUL TO'XTATILDI!</b>\n\n"
                f"Hurmatli <b>{mentor_name}</b>, siz o'qitgan <b>{sales_count} ta o'quvchi</b> uchun "
                f"<b>{total_amount:,.0f} so'm</b> royalti to'lovini kartangizdan yechib olishda xatolik yuz berdi.\n\n"
                f"❌ <b>Xatolik sababi:</b> <i>{txn_id}</i> (Hisobda mablag' yetarli emas yoki karta cheklovi)\n\n"
                f"⚠️ Qarzdorlik to'lanmaguncha <b>yangi o'quvchilarni qabul qilish vaqtincha to'xtatildi</b>. "
                f"Iltimos, kartangiz hisobini to'ldiring yoki boshqa karta ulang."
            )
            try:
                await self._userbot_client.send_message(mentor.telegram_id, fail_msg)
            except Exception as e:
                logger.warning("Mentorga xatolik xabarini yuborishda xato: %s", e)

            # 4. Super Mentor / Adminga xabar
            admin_fail_msg = (
                f"🚨 <b>MENTOR QABULI TO'XTATILDI (To'lov yechilmadi)!</b>\n\n"
                f"👤 Mentor: <b>{mentor_name}</b> (ID: <code>{mentor.telegram_id}</code>)\n"
                f"🔑 Litsenziya: Node #{node.id}\n"
                f"👥 O'qitilgan: <b>{sales_count} ta o'quvchi</b>\n"
                f"💵 Qarz: <b>{total_amount:,.0f} so'm</b>\n"
                f"❌ Xatolik: <i>{txn_id}</i>\n\n"
                f"Kartada pul yetarli bo'lmagani sababli mentorning yangi qabuli vaqtincha to'xtatildi (suspended)."
            )
            for admin_id in settings.bot.admin_ids:
                if admin_id != mentor.telegram_id:
                    try:
                        await self._userbot_client.send_message(admin_id, admin_fail_msg)
                    except Exception as e:
                        logger.warning("Adminga xatolik xabarini yuborishda xato: %s", e)

            return {"status": "payment_failed", "suspended": True, "error": txn_id}

        # To'langan deb belgilash
        await self._royalty_repo.settle_for_child_node(child_node_id)

        # Agar ilgari to'xtatilgan bo'lsa, qayta faollashtirish (active)
        if node.status != "active":
            await self._node_repo.update_status(node.id, "active")

        # Log yozish
        await self._royalty_repo.record_auto_settlement(
            node_id=node.id,
            mentor_id=mentor.id,
            amount=total_amount,
            sales_count=sales_count,
            provider=card.provider,
            external_txn_id=str(txn_id),
            status="success",
        )

        # Mentorga xabar yuborish
        debit_msg = (
            f"💳 <b>Hamkorlik bo'yicha royalti qabul qilindi!</b>\n\n"
            f"Hurmatli <b>{mentor_name}</b>, siz o'qitgan <b>{sales_count} ta o'quvchi</b> uchun "
            f"<b>{total_amount:,.0f} so'm</b> miqdoridagi royalti ulushi ulangan kartangizdan avtomatik muvaffaqiyatli yechildi.\n\n"
            f"✅ <b>Kabinetingiz to'liq faol holatda.</b> Yangi o'quvchilarni qabul qilishda davom etishingiz mumkin! 🤝"
        )
        try:
            await self._userbot_client.send_message(mentor.telegram_id, debit_msg)
        except Exception as e:
            logger.warning("Mentorga muvaffaqiyat xabarini yuborishda xato: %s", e)

        # Asosiy mentor / ota tugunni xabardor qilish
        if node.parent_id:
            parent_node = await self._node_repo.get_by_id(node.parent_id)
            if parent_node:
                parent_mentor = await self._user_repo.get_by_id(parent_node.owner_user_id)
                if parent_mentor and parent_mentor.telegram_id != mentor.telegram_id:
                    admin_msg = (
                        f"💰 <b>Royalti to'lovi qabul qilindi!</b>\n\n"
                        f"👤 Kichik mentor: <b>{mentor_name}</b>\n"
                        f"👥 Shogirdlar: <b>{sales_count} ta</b>\n"
                        f"💵 Summa: <b>{total_amount:,.0f} so'm</b>\n"
                        f"💳 Tizim: <b>{card.provider.upper()} Auto-debit</b>\n\n"
                        f"Mablag' muvaffaqiyatli hisoblandi."
                    )
                    try:
                        await self._userbot_client.send_message(parent_mentor.telegram_id, admin_msg)
                    except Exception as e:
                        logger.warning("Ota mentorga xabar yuborishda xato: %s", e)

        logger.info("Royalti avto-debit muvaffaqiyatli: node_id=%s, amount=%s, sales=%s", node.id, total_amount, sales_count)
        return {"status": "success", "amount": total_amount, "sales_count": sales_count, "txn_id": txn_id}
