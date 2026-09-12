from __future__ import annotations

import asyncio
import logging
import os
from urllib.parse import urlparse

from aiohttp import web
from pyrogram import Client

from core.config import settings
from db.database import Database
from userbot.assessment_handler import build_assessment_handlers
from userbot.channel_commands import build_channel_handlers
from userbot.relay_server import build_relay_app

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    db = Database(settings.db.path)
    await db.connect()
    await db.run_migrations(settings.db.migrations_dir)

    client = Client(
        name="bilimgo_relay_userbot",
        api_id=int(os.environ["USERBOT_API_ID"]),
        api_hash=os.environ["USERBOT_API_HASH"],
        session_string=os.environ.get("USERBOT_SESSION_STRING"),
    )
    await client.start()
    logger.info("Userbot Telegram'ga ulandi")

    mentor_userbot_id_raw = os.environ.get("MENTOR_USERBOT_ID")
    mentor_userbot_id = int(mentor_userbot_id_raw) if mentor_userbot_id_raw else None
    build_assessment_handlers(client, db.conn, mentor_userbot_id)
    logger.info("Baholash handlerlari ulandi (mentor_userbot_id=%s)", mentor_userbot_id)

    build_channel_handlers(client, db.conn)
    logger.info("Kanal darsliklari va skaner buyruqlari ulandi (.setchannel, .buildcourse, .courses)")

    app = build_relay_app(client)
    runner = web.AppRunner(app)
    await runner.setup()

    parsed = urlparse(settings.relay.internal_url)
    site = web.TCPSite(runner, host=parsed.hostname or "127.0.0.1", port=parsed.port or 8081)
    await site.start()
    logger.info("Relay server ishga tushdi: %s", settings.relay.internal_url)

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await client.stop()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

