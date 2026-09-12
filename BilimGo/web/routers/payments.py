from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse

from core.exceptions import NotFoundError
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.click_transaction_repo import ClickTransactionRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.payme_transaction_repo import PaymeTransactionRepository
from db.repositories.royalty_repo import RoyaltyLedgerRepository
from db.repositories.sale_repo import SaleRepository
from db.repositories.user_repo import UserRepository
from db.repositories.mentor_card_repo import MentorCardRepository
from services.auto_debit_service import AutoDebitService
from services.cabinet_service import CabinetService
from services.click_service import ClickService
from services.payme_service import PaymeRPCException, PaymeService
from services.payment_service import PaymentProvider, PaymentService
from services.royalty_service import RoyaltyService
from web.dependencies.auth import get_current_telegram_id

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _build_payment_service() -> PaymentService:
    conn = database.conn
    node_repo = LicenseNodeRepository(conn)
    royalty_repo = RoyaltyLedgerRepository(conn)
    user_repo = UserRepository(conn)
    card_repo = MentorCardRepository(conn)

    royalty_service = RoyaltyService(node_repo, royalty_repo)
    cabinet_service = CabinetService(
        cabinet_repo=CabinetRepository(conn),
        chat_repo=ChatRepository(conn),
        license_node_repo=node_repo,
        user_repo=user_repo,
    )
    auto_debit_service = AutoDebitService(
        node_repo=node_repo,
        royalty_repo=royalty_repo,
        card_repo=card_repo,
        user_repo=user_repo,
    )
    return PaymentService(
        course_repo=CourseRepository(conn),
        sale_repo=SaleRepository(conn),
        access_grant_repo=AccessGrantRepository(conn),
        royalty_service=royalty_service,
        cabinet_service=cabinet_service,
        user_repo=user_repo,
        auto_debit_service=auto_debit_service,
    )


@router.post("/purchase/initiate")
async def initiate_purchase(
    course_id: int,
    license_node_id: int,
    provider: PaymentProvider,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    user_repo = UserRepository(database.conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    payment_service = _build_payment_service()
    try:
        pending = await payment_service.initiate_purchase(
            student_id=user.id,
            course_id=course_id,
            license_node_id=license_node_id,
            provider=provider,
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {"sale_id": pending.sale_id, "amount": pending.amount}


@router.post("/click/prepare")
async def click_prepare(request: Request) -> JSONResponse:
    form = dict(await request.form())
    service = ClickService(
        sale_repo=SaleRepository(database.conn),
        click_txn_repo=ClickTransactionRepository(database.conn),
        payment_service=_build_payment_service(),
    )
    response = await service.prepare(form)
    return JSONResponse(response.as_dict())


@router.post("/click/complete")
async def click_complete(request: Request) -> JSONResponse:
    form = dict(await request.form())
    service = ClickService(
        sale_repo=SaleRepository(database.conn),
        click_txn_repo=ClickTransactionRepository(database.conn),
        payment_service=_build_payment_service(),
    )
    response = await service.complete(form)
    return JSONResponse(response.as_dict())


@router.post("/payme")
async def payme_rpc(request: Request) -> JSONResponse:
    body = await request.json()
    service = PaymeService(
        sale_repo=SaleRepository(database.conn),
        payme_txn_repo=PaymeTransactionRepository(database.conn),
        payment_service=_build_payment_service(),
    )
    try:
        result = await service.dispatch(body["method"], body.get("params", {}))
        return JSONResponse({"result": result, "id": body.get("id")})
    except PaymeRPCException as exc:
        return JSONResponse(
            {
                "error": {"code": exc.code, "message": exc.message},
                "id": body.get("id"),
            }
        )
