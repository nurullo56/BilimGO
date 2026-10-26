from __future__ import annotations

import logging
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.config import settings
from db.database import database
from db.repositories.mentor_card_repo import MentorCardRepository
from db.repositories.user_repo import UserRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cards", tags=["cards"])


class BindCardInitiateRequest(BaseModel):
    provider: str = Field(pattern="^(payme|click)$")
    card_number: str
    card_expire: str  # MMYY


class BindCardVerifyRequest(BaseModel):
    provider: str = Field(pattern="^(payme|click)$")
    card_token: str
    code: str
    card_number_masked: str | None = None
    card_expire: str | None = None


@router.get("/my-card")
async def get_my_card(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    card = await MentorCardRepository(conn).get_active_card(user.id)
    if not card:
        return {"has_card": False}
    return {
        "has_card": True,
        "provider": card.provider,
        "card_number_masked": card.card_number_masked,
        "card_expire": card.card_expire,
        "created_at": card.created_at,
    }


@router.post("/bind/initiate")
async def initiate_card_bind(
    body: BindCardInitiateRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """Karta ulashni boshlash (SMS kod so'rash)."""
    if settings.debug:
        mock_token = f"token_{uuid.uuid4().hex[:12]}"
        return {
            "status": "code_sent",
            "card_token": mock_token,
            "message": "SMS tasdiqlash kodi yuborildi (Debug: ixtiyoriy kod kiriting)",
        }

    # Production Payme / Click card tokenization
    if body.provider == "payme":
        # cards.create + cards.get_verify_code
        url = "https://checkout.paycom.uz/api"
        headers = {"X-Auth": f"{settings.payme.merchant_id}:{settings.payme.secret_key}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={
                    "method": "cards.create",
                    "params": {"card": {"number": body.card_number, "expire": body.card_expire}, "save": True},
                },
                headers=headers,
            )
            data = resp.json()
            if "error" in data or not data.get("result"):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(data.get("error", "Karta yaratishda xato")))

            card_token = data["result"]["card"]["token"]

            resp2 = await client.post(
                url,
                json={"method": "cards.get_verify_code", "params": {"token": card_token}},
                headers=headers,
            )
            data2 = resp2.json()
            if "error" in data2:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(data2.get("error", "SMS kod yuborishda xato")))

            return {"status": "code_sent", "card_token": card_token, "provider": "payme"}
    else:
        # Click card token request
        url = "https://api.click.uz/v2/merchant/card_token/request"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Auth": f"{settings.click.merchant_id}:{settings.click.secret_key}",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={
                    "service_id": settings.click.service_id,
                    "card_number": body.card_number,
                    "expire_date": body.card_expire,
                },
                headers=headers,
            )
            data = resp.json()
            if data.get("error_code") != 0:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=data.get("error_note", "Click karta ulashda xato"))

            return {
                "status": "code_sent",
                "card_token": data.get("card_token"),
                "provider": "click",
            }


@router.post("/bind/verify")
async def verify_card_bind(
    body: BindCardVerifyRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    """SMS kodni tasdiqlash va kartani mentor hisobiga saqlash."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    card_repo = MentorCardRepository(conn)

    masked_num = body.card_number_masked or "8600 **** **** 0000"

    if not settings.debug:
        if body.provider == "payme":
            url = "https://checkout.paycom.uz/api"
            headers = {"X-Auth": f"{settings.payme.merchant_id}:{settings.payme.secret_key}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    json={"method": "cards.verify", "params": {"token": body.card_token, "code": body.code}},
                    headers=headers,
                )
                data = resp.json()
                if "error" in data:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="SMS kod noto'g'ri")
                card_data = data.get("result", {}).get("card", {})
                masked_num = card_data.get("number", masked_num)
        else:
            url = "https://api.click.uz/v2/merchant/card_token/verify"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Auth": f"{settings.click.merchant_id}:{settings.click.secret_key}",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "service_id": settings.click.service_id,
                        "card_token": body.card_token,
                        "sms_code": body.code,
                    },
                    headers=headers,
                )
                data = resp.json()
                if data.get("error_code") != 0:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="SMS kod noto'g'ri")

    saved_card = await card_repo.save_card(
        mentor_id=user.id,
        provider=body.provider,
        card_token=body.card_token,
        card_number_masked=masked_num,
        card_expire=body.card_expire,
    )

    return {
        "status": "success",
        "message": "Karta avto-to'lov uchun muvaffaqiyatli ulandi!",
        "card_number": saved_card.card_number_masked,
    }


@router.post("/unbind")
async def unbind_card(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    """Uланган kartani mentor hisobidan uzish (faolsizlantirish)."""
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    card_repo = MentorCardRepository(conn)
    card = await card_repo.get_active_card(user.id)
    if card:
        await card_repo.deactivate_card(card.id)
        return {"status": "success", "message": "Karta muvaffaqiyatli uzildi"}
    return {"status": "not_found", "message": "Ulangan faol karta topilmadi"}
