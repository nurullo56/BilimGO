from __future__ import annotations

import asyncio
import html
import logging
import re
import aiosqlite
from pyrogram import Client, filters
from pyrogram.types import Message

logger = logging.getLogger(__name__)

MODULE_REGEX = re.compile(
    r"^(?:#?\s*(?:modul|bob|bo['`ʼ]lim)\s*(\d+)[:\s.-]*(.*)|(?:modul|bob|bo['`ʼ]lim)\s*(\d+))",
    re.IGNORECASE,
)
LESSON_REGEX = re.compile(
    r"(?:#?\s*(\d+)[-–—\s]*(?:dars|mavzu)[:\s.-]*(.*)|(?:dars|mavzu)\s*(\d+)[:\s.-]*(.*))",
    re.IGNORECASE,
)


def _extract_title(text: str, default: str) -> str:
    if not text:
        return default
    first_line = text.strip().split("\n")[0].strip()
    first_line = re.sub(r"^[#*`_]+", "", first_line).strip()
    if len(first_line) > 90:
        return first_line[:87] + "..."
    return first_line or default


def build_channel_handlers(client: Client, conn: aiosqlite.Connection) -> None:
    """Kanal skaneri, darslarni avtomatik bazaga yozish va boshqaruv komandalari."""

    @client.on_message(filters.me & filters.command("setchannel", prefixes=["."]))
    async def set_channel_cmd(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.edit_text(
                "❌ <b>Xatolik:</b> Kanal username yoki ID-sini kiriting.\n"
                "Misol: <code>.setchannel @logistika_kurs</code>"
            )
            return

        target = args[1].strip()
        await message.edit_text(f"⏳ <b>Kanal qidirilmoqda:</b> <code>{html.escape(target)}</code>...")

        try:
            chat = await client.get_chat(target)
            channel_id = chat.id
            title = chat.title or "Kanal"
            username = chat.username or ""

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS target_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    title TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            await conn.execute(
                """
                INSERT INTO target_channels (channel_id, username, title)
                VALUES (?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET username = excluded.username, title = excluded.title
                """,
                (channel_id, username, title),
            )
            await conn.commit()

            await message.edit_text(
                f"✅ <b>Kanal muvaffaqiyatli saqlandi va kuzatuvga olindi!</b>\n\n"
                f"📌 <b>Nomi:</b> {html.escape(title)}\n"
                f"🆔 <b>ID:</b> <code>{channel_id}</code>\n"
                f"🔗 <b>Username:</b> @{username or 'Yopiq kanal'}\n\n"
                f"💡 <i>Kurs yaratish va darslarni yuklash uchun:</i>\n"
                f"<code>.buildcourse 1 {target}</code>"
            )
        except Exception as exc:
            logger.exception("setchannel error")
            await message.edit_text(f"❌ <b>Xatolik:</b> {html.escape(str(exc))}")

    @client.on_message(filters.me & filters.command("buildcourse", prefixes=["."]))
    async def build_course_cmd(client: Client, message: Message):
        parts = message.text.split()
        if len(parts) < 3:
            await message.edit_text(
                "❌ <b>Xatolik:</b> Kurs ID va kanal manzilini kiriting.\n"
                "Misol: <code>.buildcourse 1 @logistika_kurs</code>"
            )
            return

        course_id_raw = parts[1]
        target = parts[2]

        if not course_id_raw.isdigit():
            await message.edit_text("❌ Kurs ID raqam bo'lishi kerak!")
            return

        course_id = int(course_id_raw)
        await message.edit_text(f"🔍 <b>Kanal tekshirilmoqda:</b> <code>{html.escape(target)}</code>...")

        try:
            chat = await client.get_chat(target)
            channel_id = chat.id

            await message.edit_text(f"📥 <b>Darsliklar kanaldan o'qilmoqda va BilimGo bazasiga yozilmoqda...</b>\nKanal: <b>{html.escape(chat.title)}</b>")

            # Eski darslarni tozalaymiz
            await conn.execute("DELETE FROM lessons WHERE course_id = ?", (course_id,))
            await conn.commit()

            count = 0
            order_index = 1

            async for msg in client.get_chat_history(channel_id, limit=300):
                text = msg.caption or msg.text or ""
                has_media = bool(msg.video or msg.voice or msg.audio or msg.document)

                if not text and not has_media:
                    continue

                first_line = text.split("\n")[0] if text else ""
                title = _extract_title(text, f"{order_index}-Dars")

                duration = 300
                if msg.video and msg.video.duration:
                    duration = msg.video.duration
                elif msg.voice and msg.voice.duration:
                    duration = msg.voice.duration
                elif msg.audio and msg.audio.duration:
                    duration = msg.audio.duration

                is_free = 1 if order_index <= 2 else 0

                await conn.execute(
                    """
                    INSERT INTO lessons (course_id, title, source_channel_id, source_message_id, duration_sec, order_index, is_free_preview)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (course_id, title, channel_id, msg.id, duration, order_index, is_free),
                )
                order_index += 1
                count += 1

            await conn.commit()

            await message.edit_text(
                f"🎉 <b>Darsliklar BilimGo bazasiga muvaffaqiyatli generatsiya qilindi!</b>\n\n"
                f"📚 <b>Kurs ID:</b> <code>{course_id}</code>\n"
                f"📢 <b>Kanal:</b> {html.escape(chat.title)}\n"
                f"📖 <b>Yuklangan darslar soni:</b> <code>{count}</code> ta\n"
                f"🎁 <b>Bepul sinov darslari:</b> Dastlabki 2 ta dars\n\n"
                f"🌐 <i>Darslar Telegram Mini App frontendida darhol paydo bo'ldi!</i>"
            )
        except Exception as exc:
            logger.exception("buildcourse error")
            await message.edit_text(f"❌ <b>Xatolik:</b> {html.escape(str(exc))}")

    @client.on_message(filters.me & filters.command("courses", prefixes=["."]))
    async def list_courses_cmd(client: Client, message: Message):
        cursor = await conn.execute(
            """
            SELECT c.id, c.title, c.base_price, COUNT(l.id) AS lessons_count
            FROM courses c
            LEFT JOIN lessons l ON l.course_id = c.id
            GROUP BY c.id, c.title, c.base_price
            ORDER BY c.id ASC
            """
        )
        rows = await cursor.fetchall()

        if not rows:
            await message.edit_text("📚 Bazada hozircha kurslar mavjud emas.")
            return

        lines = ["<b>📚 BilimGo Platformasi Kurslari:</b>\n"]
        for r in rows:
            lines.append(f"• <b>#{r['id']}: {html.escape(r['title'])}</b>\n   ├ Darslar: <b>{r['lessons_count']} ta</b>\n   └ Narxi: <b>{r['base_price']:,.0f} so'm</b>")

        await message.edit_text("\n\n".join(lines))

    @client.on_message(filters.me & filters.command("stats", prefixes=["."]))
    async def stats_cmd(client: Client, message: Message):
        cursor = await conn.execute("SELECT COUNT(*) AS c FROM courses")
        c_count = (await cursor.fetchone())["c"]

        cursor = await conn.execute("SELECT COUNT(*) AS l FROM lessons")
        l_count = (await cursor.fetchone())["l"]

        cursor = await conn.execute("SELECT COUNT(*) AS u FROM users")
        u_count = (await cursor.fetchone())["u"]

        await message.edit_text(
            f"📊 <b>BilimGo Tizim Statistikasi:</b>\n\n"
            f"📚 <b>Jami Kurslar:</b> <code>{c_count}</code> ta\n"
            f"📖 <b>Jami Darslar:</b> <code>{l_count}</code> ta\n"
            f"👥 <b>Foydalanuvchilar:</b> <code>{u_count}</code> ta\n\n"
            f"⚡️ <i>Zero-Storage Streaming & Relay: Faol</i>"
        )

    @client.on_message(filters.me & filters.command("help", prefixes=["."]))
    async def help_cmd(client: Client, message: Message):
        await message.edit_text(
            "🤖 <b>BilimGo UserBot Boshqaruv Buyruqlari:</b>\n\n"
            "🔹 <code>.setchannel &lt;@kanal&gt;</code> — Kanalni kuzatuvga qo'shadi.\n"
            "🔹 <code>.buildcourse &lt;kurs_id&gt; &lt;@kanal&gt;</code> — Kanaldagi postlarni BilimGo darslariga aylantiradi.\n"
            "🔹 <code>.courses</code> — Barcha LMS kurslari va darslar sonini ko'rish.\n"
            "🔹 <code>.stats</code> — Tizim umumiy statistikasini ko'rish.\n"
            "🔹 <code>.help</code> — Ushbu qo'llanmani chiqarish."
        )
