from __future__ import annotations

import time
from typing import Any

from db.database import database
from db.repositories.payme_transaction_repo import PaymeTransactionRepository
from db.repositories.sale_repo import SaleRepository
from services.payment_service import PaymentService


class PaymeError:
    INVALID_AMOUNT = -31001
    TRANSACTION_NOT_FOUND = -31003
    CANNOT_CANCEL = -31007
    CANNOT_PERFORM = -31008
    ORDER_NOT_FOUND = -31050


class PaymeRPCException(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


PAYME_STATE_CREATED = 1
PAYME_STATE_PERFORMED = 2
PAYME_STATE_CANCELLED_AFTER_CREATE = -1
PAYME_STATE_CANCELLED_AFTER_PERFORM = -2


class PaymeService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        payme_txn_repo: PaymeTransactionRepository,
        payment_service: PaymentService,
    ) -> None:
        self._sale_repo = sale_repo
        self._payme_txn_repo = payme_txn_repo
        self._payment_service = payment_service

    async def dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "CheckPerformTransaction": self._check_perform,
            "CreateTransaction": self._create,
            "PerformTransaction": self._perform,
            "CancelTransaction": self._cancel,
            "CheckTransaction": self._check,
        }
        handler = handlers.get(method)
        if handler is None:
            raise PaymeRPCException(-32601, "Method topilmadi")
        return await handler(params)

    async def _resolve_sale(self, params: dict[str, Any]):
        sale_id = params.get("account", {}).get("sale_id")
        if sale_id is None:
            raise PaymeRPCException(PaymeError.ORDER_NOT_FOUND, "sale_id ko'rsatilmagan")
        sale = await self._sale_repo.get_by_id(int(sale_id))
        if sale is None:
            raise PaymeRPCException(PaymeError.ORDER_NOT_FOUND, "Buyurtma topilmadi")
        return sale

    async def _check_perform(self, params: dict[str, Any]) -> dict[str, Any]:
        sale = await self._resolve_sale(params)
        amount_tiyin = int(params["amount"])
        if abs(sale.amount * 100 - amount_tiyin) > 1:
            raise PaymeRPCException(PaymeError.INVALID_AMOUNT, "Summa mos emas")
        return {"allow": True}

    async def _create(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params["id"]
        existing = await self._payme_txn_repo.get_by_id(payme_id)
        if existing is not None:
            if existing.state != PAYME_STATE_CREATED:
                raise PaymeRPCException(PaymeError.CANNOT_PERFORM, "Holat mos emas")
            return {
                "create_time": existing.create_time,
                "transaction": str(existing.id),
                "state": existing.state,
            }

        sale = await self._resolve_sale(params)
        amount_tiyin = int(params["amount"])
        if abs(sale.amount * 100 - amount_tiyin) > 1:
            raise PaymeRPCException(PaymeError.INVALID_AMOUNT, "Summa mos emas")

        create_time = int(time.time() * 1000)
        await self._payme_txn_repo.create(
            payme_id=payme_id,
            sale_id=sale.id,
            amount=sale.amount,
            create_time=create_time,
        )
        return {"create_time": create_time, "transaction": payme_id, "state": PAYME_STATE_CREATED}

    async def _perform(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params["id"]
        txn = await self._payme_txn_repo.get_by_id(payme_id)
        if txn is None:
            raise PaymeRPCException(PaymeError.TRANSACTION_NOT_FOUND, "Tranzaksiya topilmadi")

        if txn.state == PAYME_STATE_PERFORMED:
            return {
                "transaction": payme_id, "state": txn.state, "perform_time": txn.perform_time,
            }
        if txn.state != PAYME_STATE_CREATED:
            raise PaymeRPCException(PaymeError.CANNOT_PERFORM, "Holat mos emas")

        perform_time = int(time.time() * 1000)
        async with database.transaction():
            await self._payme_txn_repo.mark_performed(payme_id, perform_time)
            await self._payment_service.confirm_payment(sale_id=txn.sale_id, external_txn_id=payme_id)

        return {"transaction": payme_id, "state": PAYME_STATE_PERFORMED, "perform_time": perform_time}

    async def _cancel(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params["id"]
        reason = int(params.get("reason", 0))
        txn = await self._payme_txn_repo.get_by_id(payme_id)
        if txn is None:
            raise PaymeRPCException(PaymeError.TRANSACTION_NOT_FOUND, "Tranzaksiya topilmadi")

        cancel_time = int(time.time() * 1000)
        new_state = (
            PAYME_STATE_CANCELLED_AFTER_PERFORM
            if txn.state == PAYME_STATE_PERFORMED
            else PAYME_STATE_CANCELLED_AFTER_CREATE
        )
        if txn.state not in (PAYME_STATE_CREATED, PAYME_STATE_PERFORMED):
            return {"transaction": payme_id, "state": txn.state, "cancel_time": txn.cancel_time}

        await self._payme_txn_repo.mark_cancelled(payme_id, cancel_time, reason, new_state)
        if new_state == PAYME_STATE_CANCELLED_AFTER_PERFORM:
            await self._sale_repo.mark_refunded(txn.sale_id)

        return {"transaction": payme_id, "state": new_state, "cancel_time": cancel_time}

    async def _check(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params["id"]
        txn = await self._payme_txn_repo.get_by_id(payme_id)
        if txn is None:
            raise PaymeRPCException(PaymeError.TRANSACTION_NOT_FOUND, "Tranzaksiya topilmadi")
        return {
            "create_time": txn.create_time,
            "perform_time": txn.perform_time,
            "cancel_time": txn.cancel_time,
            "transaction": payme_id,
            "state": txn.state,
            "reason": txn.reason,
        }
