from __future__ import annotations

import logging

from aiohttp import web
from pyrogram import Client
from pyrogram.errors import RPCError

from core.config import settings

logger = logging.getLogger(__name__)


def _check_secret(request: web.Request) -> None:
    if request.headers.get("X-Internal-Secret") != settings.relay.internal_secret:
        raise web.HTTPUnauthorized(reason="Ichki token noto'g'ri")


def build_relay_app(client: Client) -> web.Application:
    app = web.Application()

    async def meta_handler(request: web.Request) -> web.Response:
        _check_secret(request)
        channel_id = int(request.query["channel_id"])
        message_id = int(request.query["message_id"])

        try:
            message = await client.get_messages(channel_id, message_id)
        except RPCError as exc:
            logger.error("get_messages xato: %s", exc)
            raise web.HTTPBadGateway(reason="Manba xabar topilmadi") from exc

        media = message.video or message.document
        if media is None:
            raise web.HTTPNotFound(reason="Xabarda video/fayl yo'q")

        return web.json_response({"file_size": media.file_size})

    async def relay_handler(request: web.Request) -> web.StreamResponse:
        _check_secret(request)
        channel_id = int(request.query["channel_id"])
        message_id = int(request.query["message_id"])
        offset_chunk = int(request.query.get("offset_chunk", 0))

        try:
            message = await client.get_messages(channel_id, message_id)
        except RPCError as exc:
            logger.error("get_messages xato: %s", exc)
            raise web.HTTPBadGateway(reason="Manba xabar topilmadi") from exc

        response = web.StreamResponse(
            status=200, headers={"Content-Type": "application/octet-stream"}
        )
        await response.prepare(request)

        async for chunk in client.stream_media(message, offset=offset_chunk):
            await response.write(chunk)

        await response.write_eof()
        return response

    async def send_message_handler(request: web.Request) -> web.Response:
        _check_secret(request)
        data = await request.json()
        recipient_telegram_id = data.get("recipient_telegram_id")
        text = data.get("text")
        if not recipient_telegram_id or not text:
            raise web.HTTPBadRequest(reason="recipient_telegram_id va text majburiy")

        try:
            from pyrogram.enums import ParseMode
            sent = await client.send_message(
                chat_id=int(recipient_telegram_id),
                text=str(text),
                parse_mode=ParseMode.HTML,
            )
            logger.info(
                "Userbot orqali xabar yuborildi: recipient=%s message_id=%s",
                recipient_telegram_id, sent.id,
            )
            return web.json_response({"success": True, "message_id": sent.id})
        except Exception as exc:
            logger.error(
                "Userbot orqali xabar yuborishda xato (recipient=%s): %s",
                recipient_telegram_id, exc,
            )
            return web.json_response({"success": False, "error": str(exc)}, status=500)

    app.router.add_get("/meta", meta_handler)
    app.router.add_get("/relay", relay_handler)
    app.router.add_post("/send_message", send_message_handler)
    return app
