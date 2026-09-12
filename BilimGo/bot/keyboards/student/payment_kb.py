from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_checkout_payment_keyboard(provider: str, checkout_url: str) -> InlineKeyboardMarkup:
    """To'lov havolasiga o'tish tugmasi."""
    provider_title = provider.capitalize()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 {provider_title} orqali to'lash", url=checkout_url)]
        ]
    )
