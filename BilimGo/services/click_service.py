from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from core.config import settings
from db.database import database
from db.repositories.click_transaction_repo import ClickTransactionRepository
from db.repositories.sale_repo import SaleRepository
from services.payment_service import PaymentService


class ClickError:
    SUCCESS = 0
    SIGN_FAILED = -1
    INVALID_AMOUNT = -2
    ACTION_NOT_FOUND = -3
    ALREADY_PAID = -4
    USER_NOT_FOUND = -5
    TRANSACTION_NOT_FOUND = -6
    TRANSACTION_CANCELLED = -9


@dataclass(slots=True)
class ClickResponse:
    click_trans_id: str
    merchant_trans_id: str
    merchant_prepare_id: str | None
    merchant_confirm_id: str | None
    error: int
    error_note: str

    def as_dict(self) -> dict:
        payload = {
            "click_trans_id": self.click_trans_id,
            "merchant_trans_id": self.merchant_trans_id,
            "error": self.error,
            "error_note": self.error_note,
        }
        if self.merchant_prepare_id is not None:
            payload["merchant_prepare_id"] = self.merchant_prepare_id
        if self.merchant_confirm_id is not None:
            payload["merchant_confirm_id"] = self.merchant_confirm_id
        return payload


class ClickService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        click_txn_repo: ClickTransactionRepository,
        payment_service: PaymentService,
    ) -> None:
        self._sale_repo = sale_repo
        self._click_txn_repo = click_txn_repo
        self._payment_service = payment_service

    @staticmethod
    def _verify_prepare_sign(params: dict) -> bool:
        raw = (
            f"{params['click_trans_id']}{params['service_id']}"
            f"{settings.click.secret_key}{params['merchant_trans_id']}"
            f"{params['amount']}{params['action']}{params['sign_time']}"
        )
        expected = hashlib.md5(raw.encode()).hexdigest()
        return hmac.compare_digest(expected, str(params.get("sign_string", "")))

    @staticmethod
    def _verify_complete_sign(params: dict) -> bool:
        raw = (
            f"{params['click_trans_id']}{params['service_id']}"
            f"{settings.click.secret_key}{params['merchant_trans_id']}"
            f"{params.get('merchant_prepare_id', '')}"
            f"{params['amount']}{params['action']}{params['sign_time']}"
        )
        expected = hashlib.md5(raw.encode()).hexdigest()
        return hmac.compare_digest(expected, str(params.get("sign_string", "")))

    async def prepare(self, params: dict) -> ClickResponse:
        merchant_trans_id = params["merchant_trans_id"]

        if not self._verify_prepare_sign(params):
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.SIGN_FAILED, "Sign xato",
            )

        sale = await self._sale_repo.get_by_id(int(merchant_trans_id))
        if sale is None:
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.USER_NOT_FOUND, "Sale topilmadi",
            )

        if abs(sale.amount - float(params["amount"])) > 0.01:
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.INVALID_AMOUNT, "Summa mos emas",
            )

        if sale.payment_status == "paid":
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.ALREADY_PAID, "Allaqachon to'langan",
            )

        await self._click_txn_repo.create_if_absent(
            click_trans_id=params["click_trans_id"],
            sale_id=sale.id,
            prepare_id=str(sale.id),
            amount=sale.amount,
        )

        return ClickResponse(
            params["click_trans_id"], merchant_trans_id, str(sale.id), None,
            ClickError.SUCCESS, "OK",
        )

    async def complete(self, params: dict) -> ClickResponse:
        merchant_trans_id = params["merchant_trans_id"]

        if not self._verify_complete_sign(params):
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.SIGN_FAILED, "Sign xato",
            )

        sale = await self._sale_repo.get_by_id(int(merchant_trans_id))
        if sale is None:
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.TRANSACTION_NOT_FOUND, "Sale topilmadi",
            )

        if int(params.get("error", 0)) < 0:
            return ClickResponse(
                params["click_trans_id"], merchant_trans_id, None, None,
                ClickError.TRANSACTION_CANCELLED, "Click tomonidan bekor qilindi",
            )

        if sale.payment_status != "paid":
            async with database.transaction():
                await self._payment_service.confirm_payment(
                    sale_id=sale.id, external_txn_id=params["click_trans_id"]
                )
                await self._click_txn_repo.mark_confirmed(params["click_trans_id"])

        return ClickResponse(
            params["click_trans_id"], merchant_trans_id, None, str(sale.id),
            ClickError.SUCCESS, "OK",
        )
