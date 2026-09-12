# BilimGo

Multi-tenant adaptiv ta'lim platformasi — franshiza (litsenziya daraxti), zero-storage
video delivery, AI-baholash asosidagi moslashuvchan o'quv sur'ati va real-time
mentor-talaba muloqoti.

## Arxitektura

Beshta mustaqil process bitta SQLite fayl (WAL mode) ustida ishlaydi:

| Process | Vazifa | Kirish nuqtasi |
|---|---|---|
| **bot** | Telegram bot (aiogram) — ro'yxatdan o'tish, katalog, xarid, kabinet | `bot/main.py` |
| **web** | FastAPI — video stream, to'lov webhooklari, chat, live, analytics API | `web/main.py` |
| **userbot** | Pyrogram — video relay (zero-storage) + mentor baholash handler | `userbot/main.py` |
| **ai_worker** | Claude API orqali talaba javoblarini baholaydi | `workers/ai_evaluation_worker.py` |
| **engagement_worker** | Faolsizlikni kuzatadi, nudge xabarlarini yuboradi | `workers/engagement_monitor_worker.py` |

Modullar: `core/` (config), `db/` (repository qatlami + migratsiyalar),
`services/` (biznes-mantiq), `bot/` `web/` `userbot/` (kirish nuqtalari).

## Talablar

- Python 3.12+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Telegram API ID/HASH ([my.telegram.org](https://my.telegram.org)) — userbot uchun
- Pyrogram session string (mentor userbot uchun, `Pyrogram` orqali generatsiya qilinadi)
- Click va/yoki Payme merchant ma'lumotlari
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

## Lokal ishga tushirish (Docker'siz)

```bash
git clone <repo>
cd BilimGo
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env faylini to'ldiring (pastga qarang)

# Har birini alohida terminalda ishga tushiring:
python -m bot.main
uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload
python -m userbot.main
python -m workers.ai_evaluation_worker
python -m workers.engagement_monitor_worker
```

Migratsiyalar har bir process ishga tushganda avtomatik qo'llanadi
(`db/database.py` — `schema_migrations` jadvali orqali idempotent).

## Docker orqali ishga tushirish

```bash
cp .env.example .env
# .env faylini to'ldiring

cd docker
docker compose up -d --build
docker compose logs -f
```

**Muhim:** Docker'da `RELAY_INTERNAL_URL` avtomatik `http://userbot:8081` ga
o'rnatiladi (`docker-compose.yml` ichida) — bu servislar bir-birini konteyner
nomi orqali topishi uchun. Lokal (Docker'siz) ishga tushirishda esa
`.env` faylida `http://127.0.0.1:8081` qoldiring.

SQLite fayli `bilimgo_data` nomli Docker volume'da saqlanadi — konteynerlar
qayta qurilganda ma'lumot yo'qolmaydi.

## .env sozlamalari

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | @BotFather bergan token |
| `ADMIN_IDS` | Vergul bilan ajratilgan Telegram ID'lar (super admin) |
| `DB_PATH` | SQLite fayl yo'li (default: `data/bilimgo.db`) |
| `RELAY_INTERNAL_URL` | web ↔ userbot ichki aloqa manzili |
| `RELAY_INTERNAL_SECRET` | Ichki so'rovlarni himoyalovchi maxfiy kalit |
| `DELIVERY_TOKEN_TTL_SECONDS` | Video token amal qilish muddati (soniya) |
| `USERBOT_API_ID` / `USERBOT_API_HASH` | my.telegram.org'dan olingan |
| `USERBOT_SESSION_STRING` | Pyrogram session (bir marta generatsiya qilinadi) |
| `MENTOR_USERBOT_ID` | Ushbu userbot qaysi mentorga tegishli (DB id) |
| `CLICK_*` / `PAYME_*` | To'lov provayder ma'lumotlari |
| `ANTHROPIC_API_KEY` | Claude API kaliti (AI baholash uchun) |
| `ANTHROPIC_MODEL` | Model nomi (default: `claude-sonnet-5`) |
| `WEBAPP_BASE_URL` | Frontend joylashgan domen (bot havolalar shu asosda quriladi) |

## Pyrogram session string generatsiya qilish

```python
from pyrogram import Client

with Client("bilimgo_relay_userbot", api_id=YOUR_API_ID, api_hash="YOUR_API_HASH") as app:
    print(app.export_session_string())
```

Chiqqan qatorni `.env` faylidagi `USERBOT_SESSION_STRING` ga qo'ying.

## Loyiha holati

✅ To'liq ishlaydigan va test qilingan backend: poydevor, video relay,
to'lov (Click/Payme) + royalty, kabinet/chat, mentor userbot + AI baholash +
adaptive unlock, live darslar + analytics + engagement nudge, bot handlerlari.

⏳ Hali qo'shilmagan: WebApp frontend (video player, chat UI, kabinet sahifasi),
to'liq admin panel, HTTPS/reverse proxy sozlamalari (production uchun Nginx +
Let's Encrypt tavsiya etiladi).

## Litsenziya

Xususiy loyiha — barcha huquqlar himoyalangan.
