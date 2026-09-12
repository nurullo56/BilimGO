"""
BilimGo Course Synchronizer
UserBot orqali yuklangan kanal darsliklarini BilimGo platformasi bazasiga avtomatik ulash va sinxronlash.
"""

from __future__ import annotations
import os
import re
import sqlite3
import sys
from pathlib import Path

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
BILIMGO_DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "bilimgo.db")))
USERBOT_DB_PATH = Path(os.getenv("USERBOT_DB_PATH", str(BASE_DIR.parent / "BilimGoUserBot" / "BilimGoUserBot" / "userbot_database.db")))
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR", str(BASE_DIR.parent / "BilimGoUserBot" / "BilimGoUserBot" / "downloads")))


def extract_title(text: str, default: str) -> str:
    if not text:
        return default
    first_line = text.strip().split("\n")[0].strip()
    first_line = re.sub(r"^[#*`_]+", "", first_line).strip()
    first_line = re.sub(r"^[0-9]+[-–—\s.:)]*", "", first_line).strip()
    if len(first_line) > 85:
        return first_line[:82] + "..."
    return first_line or default


def get_media_duration(file_path: Path | None) -> int:
    if not file_path or not file_path.exists():
        return 300
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_path.suffix.lower() in [".oga", ".ogg", ".opus"]:
            return max(60, int(size_mb * 120))
        elif file_path.suffix.lower() in [".mp4", ".mov", ".webm"]:
            return max(120, int(size_mb * 18))
    except Exception as exc:
        import logging
        logging.exception("Jim xatolik (Swallowed Exception): %s", exc)
    return 300


def sync_all_courses():
    if not BILIMGO_DB_PATH.exists():
        print(f"BilimGo DB topilmadi: {BILIMGO_DB_PATH}")
        return

    if not USERBOT_DB_PATH.exists():
        print(f"UserBot DB topilmadi: {USERBOT_DB_PATH}")
        return

    bg_conn = sqlite3.connect(str(BILIMGO_DB_PATH))
    bg_conn.row_factory = sqlite3.Row
    
    ub_conn = sqlite3.connect(str(USERBOT_DB_PATH))
    ub_conn.row_factory = sqlite3.Row

    print("==================================================")
    print("🚀 BilimGo <-> UserBot Kurslarni Sinxronlash")
    print("==================================================")

    channels = ub_conn.execute("SELECT * FROM target_channels WHERE is_active = 1").fetchall()
    print(f"📡 UserBotda {len(channels)} ta faol kanal topildi.")

    channel_course_map = {
        -1003931379702: {
            "id": 1,
            "title": "Logistika Asoslari",
            "description": "Logistika va dispetcherlik bo'yicha to'liq amaliy qo'llanma va darsliklar.",
            "base_price": 180000.0,
        },
        -1004470592205: {
            "id": 2,
            "title": "Telegram Ads Pro",
            "description": "Telegram Ads platformasida reklama berish, Fragment, TON hamyon va tahlil bo'yicha mukammal kurs.",
            "base_price": 190000.0,
        },
        -1004475383846: {
            "id": 3,
            "title": "Telegram Ads Asoslari",
            "description": "Telegram reklama tizimi bilan ishlash bo'yicha boshlang'ich amaliyot.",
            "base_price": 150000.0,
        },
    }

    for ch in channels:
        ch_id = ch["channel_id"]
        ch_title = ch["title"] or f"Kanal {ch_id}"
        
        info = channel_course_map.get(ch_id)
        if not info:
            cursor = bg_conn.execute(
                "INSERT INTO courses (title, description, base_price, status) VALUES (?, ?, ?, 'published')",
                (ch_title, f"{ch_title} bo'yicha to'liq amaliy darslar to'plami.", 150000.0)
            )
            bg_conn.commit()
            course_id = cursor.lastrowid
            course_title = ch_title
        else:
            course_id = info["id"]
            course_title = info["title"]
            existing = bg_conn.execute("SELECT id FROM courses WHERE id = ?", (course_id,)).fetchone()
            if not existing:
                bg_conn.execute(
                    "INSERT INTO courses (id, title, description, base_price, status) VALUES (?, ?, ?, ?, 'published')",
                    (course_id, course_title, info["description"], info["base_price"])
                )
            else:
                bg_conn.execute(
                    "UPDATE courses SET title = ?, description = ?, base_price = ?, status = 'published' WHERE id = ?",
                    (course_title, info["description"], info["base_price"], course_id)
                )
            bg_conn.commit()

        posts = ub_conn.execute(
            "SELECT * FROM posts WHERE channel_id = ? ORDER BY message_id ASC",
            (ch_id,)
        ).fetchall()

        if not posts:
            print(f"⚠️ Kanal #{ch_id} ({course_title}) da postlar topilmadi.")
            continue

        lessons_to_add = []
        
        if ch_id == -1004470592205:
            # Telegram Ads Pro kanali uchun to'liq darslar
            p25 = next((p for p in posts if p["message_id"] == 25), None)
            if p25:
                lessons_to_add.append({
                    "title": "1-Dars: Kirish — Ads Telegram Target nima va qancha pul kiritiladi?",
                    "source_message_id": 25,
                    "duration_sec": 360,
                })
            
            p9 = next((p for p in posts if p["message_id"] == 9), None)
            if p9:
                lessons_to_add.append({
                    "title": "2-Dars: Maqsadli auditoriyani izlash va kanal tahlili (TgStat)",
                    "source_message_id": 9,
                    "duration_sec": 420,
                })

            step_titles = {
                10: "3-Dars (#1-bosqich): Fragment.com orqali akkaunt ochish",
                11: "4-Dars (#2-bosqich): Fragment bilan Telegram Ads hisobini ulash",
                12: "5-Dars (#3-bosqich): Kripto hamyon (Wallet) ochish",
                14: "6-Dars (#4-5-bosqich): Shaxsni tasdiqlash va ro'yxatdan o'tish",
                15: "7-Dars (#6-bosqich): TON hamyondan to'liq o'tish va Viza karta ulash",
                16: "8-Dars (#7-bosqich): TON sotib olish jarayoni (Humo karta orqali)",
                17: "9-Dars: TON sotib olishning muqobil usuli (Paynet / Uzcard)",
                18: "10-Dars (#8-bosqich): Kriptodan asosiy TON balansga o'tkazish",
                19: "11-Dars (#9-bosqich): Telegram Ads byudjetiga TON o'tkazish",
                20: "12-Dars (#10-bosqich): Telegram Ads da ilk reklamani yoqish",
                21: "13-Dars: Reklama rad qilinganida xatolarni bartaraf etish",
                22: "14-Dars: Reklama faollashishi, statistika va tahlil",
                23: "15-Dars: TON sotib olish yangilangan tartibi (USDT -> TON)",
            }
            
            for msg_id, title in step_titles.items():
                p = next((p for p in posts if p["message_id"] == msg_id), None)
                if p:
                    f_path = DOWNLOADS_DIR / str(ch_id) / f"msg_{msg_id}.mp4"
                    dur = get_media_duration(f_path)
                    lessons_to_add.append({
                        "title": title,
                        "source_message_id": msg_id,
                        "duration_sec": dur,
                    })

        elif ch_id == -1003931379702:
            order = 1
            for p in posts:
                m_type = p["media_type"]
                if m_type in ("video", "voice", "audio") or (p["file_path"] and not p["file_path"].endswith((".jpg", ".png", ".jpeg"))):
                    t = extract_title(p["text"], f"{order}-Dars")
                    f_path = DOWNLOADS_DIR / str(ch_id) / f"msg_{p['message_id']}.mp4"
                    if not f_path.exists():
                        f_path = DOWNLOADS_DIR / str(ch_id) / f"msg_{p['message_id']}.oga"
                    dur = get_media_duration(f_path)
                    lessons_to_add.append({
                        "title": t,
                        "source_message_id": p["message_id"],
                        "duration_sec": dur,
                    })
                    order += 1
        else:
            order = 1
            for p in posts:
                m_type = p["media_type"]
                if m_type in ("video", "voice", "audio"):
                    t = extract_title(p["text"], f"{order}-Dars")
                    f_path = Path(p["file_path"]) if p["file_path"] else None
                    dur = get_media_duration(f_path)
                    lessons_to_add.append({
                        "title": t,
                        "source_message_id": p["message_id"],
                        "duration_sec": dur,
                    })
                    order += 1

        if not lessons_to_add:
            print(f"⚠️ Kanal #{ch_id} uchun yaroqli darslar topilmadi.")
            continue

        bg_conn.execute("DELETE FROM lessons WHERE course_id = ?", (course_id,))
        for idx, item in enumerate(lessons_to_add, 1):
            is_free = 1 if idx <= 2 else 0
            bg_conn.execute(
                """
                INSERT INTO lessons (course_id, title, order_index, source_channel_id, source_message_id, duration_sec, is_free_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (course_id, item["title"], idx, ch_id, item["source_message_id"], item["duration_sec"], is_free)
            )
        bg_conn.commit()

        ub_conn.execute("DELETE FROM lessons WHERE course_id = ? OR source_channel_id = ?", (course_id, ch_id))
        for idx, item in enumerate(lessons_to_add, 1):
            is_free = 1 if idx <= 2 else 0
            ub_conn.execute(
                """
                INSERT INTO lessons (course_id, title, order_index, source_channel_id, source_message_id, duration_sec, is_free_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (course_id, item["title"], idx, ch_id, item["source_message_id"], item["duration_sec"], is_free)
            )
        ub_conn.commit()

        print(f"✅ Kurs #{course_id} ('{course_title}') muvaffaqiyatli ulandi!")
        print(f"   ├ Kanal: {ch_id}")
        print(f"   ├ Darslar soni: {len(lessons_to_add)} ta")
        print(f"   └ Bepul darslar: Dastlabki 2 ta dars")

    bg_conn.close()
    ub_conn.close()
    print("\n🎉 Barcha kurslar va darsliklar BilimGo platformasiga to'liq ulandi va saqlandi!")


if __name__ == "__main__":
    sync_all_courses()
