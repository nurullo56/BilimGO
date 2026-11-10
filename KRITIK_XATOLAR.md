Siz tajribali Senior Python/TypeScript dasturchisiz. Quyidagi loyihada 
production'ga chiqishdan oldin zudlik bilan tuzatilishi shart bo'lgan 
5 ta kritik xato bor. Har birini ketma-ket, ehtiyotkorlik bilan tuzat.

## LOYIHA HAQIDA QISQA KONTEKST
- Backend: Python 3.11+, FastAPI, Aiogram 3, aiosqlite (SQLite WAL)
- Frontend: React 19, Vite, TypeScript
- Arxitektura: Clean Architecture (Repository → Service → Router)
- Bot, Web, Userbot, Workerlar bitta DB ustida ishlaydi

## QAT'IY QOIDALAR (BUZILMASIN!)
1. Hech qanday biznes-logikani o'zgartirmang — faqat xatoni tuzating
2. API shartnomalarini (request/response formatlarini) saqlang
3. Har bir o'zgarishdan keyin `python -m py_compile <fayl>` bilan sintaksisni tekshiring
4. Frontend o'zgarishlaridan keyin `npm run build` ishlashini tekshiring
5. Har bir tuzatishdan keyin qaysi fayl, qaysi qator, nima o'zgarganini hisobot bering
6. Mavjud testlarni buzmang — `pytest BilimGo/tests/` o'tishi shart

---

## 🔴 XATO #1: `ai_tutor_service.py` — Mavjud bo'lmagan metod nomi

**Fayl:** `BilimGo/services/ai_tutor_service.py`

**Muammo:** Kodda `self._criteria_repo.get_by_lesson_id(lesson_id)` chaqirilgan.
Lekin `AssessmentCriteriaRepository` da bunday metod YO'Q — mavjud metod nomi
`get_by_lesson(lesson_id)`.

**Natija:** AI Ustoz har safar chaqirilganda `AttributeError: 'AssessmentCriteriaRepository' object has no attribute 'get_by_lesson_id'` → butun AI xizmati ishlamaydi.

**Tuzatish:**
1. `ai_tutor_service.py` faylida `get_by_lesson_id` ni topib, `get_by_lesson` ga almashtiring
2. Butun loyiha bo'ylab `get_by_lesson_id` chaqiruvlarini qidiring (`grep -rn "get_by_lesson_id"`) — boshqa joyda ham bo'lsa, ularni ham tuzating
3. Test yozing: `tests/test_ai_tutor_service.py` da `ask_tutor` metodini mock repo bilan chaqirib, `get_by_lesson` to'g'ri chaqirilishini tasdiqlang

---

## 🔴 XATO #2: `player.py` — Hardcoded Windows yo'llari

**Fayl:** `BilimGo/web/routers/player.py`

**Muammo:** `_get_candidate_download_folders()` funksiyasida quyidagi qatorlar bor:
```python
base_dirs = [
    Path("C:/Users/Acer/Downloads/BilimGoUserBot/BilimGoUserBot/downloads"),
    Path("C:/Users/Acer/Downloads/BilimGoUserBot/downloads"),
    settings.paths.downloads_dir,
    Path(__file__).resolve().parents[3] / "BilimGoUserBot" / "BilimGoUserBot" / "downloads",
    Path(__file__).resolve().parents[4] / "BilimGoUserBot" / "BilimGoUserBot" / "downloads",
    Path(__file__).resolve().parents[2] / "data" / "downloads",
]
Linux/Docker serverda C:/Users/Acer/... mavjud emas → videolar topilmaydi → barcha darslar ishlamaydi.

Tuzatish:

Barcha C:/Users/Acer/... hardcoded yo'llarni butunlay o'chirib tashlang

Faqat quyidagilarni qoldiring (prioritet tartibida):

settings.paths.downloads_dir (asosiy, .env dan boshqariladi)

Path(os.getenv("DOWNLOADS_DIR", "data/downloads")) (zaxira)

Path(__file__).resolve().parents[2] / "data" / "downloads" (lokal dev)

Agar lesson_repo.get_source_post_text() da ham shunga o'xshash hardcoded yo'l bo'lsa — ularni ham tuzating

_find_local_media() va _find_lesson_images() funksiyalari _get_candidate_download_folders() dan foydalanadi — ularni ham tekshiring

Butun loyiha bo'ylab C:/Users/Acer va C:\\Users\\Acer qidirib toping (grep -rn "Users/Acer") — barchasini tozalang

Natija: Docker/Linux serverda ham videolar to'g'ri topiladi.

🔴 XATO #3: frontend/server.ts — Mavjud bo'lmagan Gemini model
Fayl: frontend/server.ts

Muammo: Kodda model: 'gemini-3.7-flash' deb yozilgan. Bunday model Google Gemini API da MAVJUD EMAS.

Natija: Frontend serverdagi /api/ai/ask-lesson endpoint har safar 404 xatosi qaytaradi → AI Ustoz ishlamaydi.

Tuzatish:

frontend/server.ts faylida gemini-3.7-flash ni gemini-2.0-flash ga almashtiring (bu eng barqaror va tezkor model)

Xuddi shu faylda boshqa gemini-* model nomlari bo'lsa, ularni ham tekshirib, haqiqiy mavjud modelga almashtiring

Backend core/config.py va .env da GEMINI_MODEL qiymatini ham tekshiring — u gemini-2.0-flash bo'lishi kerak

frontend/package.json da "name": "react-example" ni "name": "bilimgo-frontend" ga o'zgartiring (bu ham AI Studio'dan qolgan iz)

Natija: Frontend AI endpoint ishlaydi.

🔴 XATO #4: getTelegramUser() — Production'da avtomatik admin fallback
Fayl: frontend/src/services/telegram.ts

Muammo: Quyidagi kod bor:

typescript
export function getTelegramUser(): TelegramUser | null {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user;
  }
  // Fallback demo user for local browser dev/testing (Admin telegram_id)
  return {
    id: 1467675358,  // ← BU ADMIN TELEGRAM ID!
    first_name: 'Nurulloh',
    last_name: 'Habibullayev',
    username: 'nurulloh_bilimgo',
    language_code: 'uz'
  };
}
Natija: Agar WebApp Telegram tashqarisida ochilsa (masalan, brauzerda to'g'ridan-to'g'ri URL'ga kirsa) — avtomatik ADMIN sifatida tizimga kiradi. Bu xavfsizlik tuynugi.

Tuzatish:

Fallback'ni faqat DEV muhitda qoldiring:

typescript
export function getTelegramUser(): TelegramUser | null {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user;
  }
  
  // Faqat lokal development uchun demo foydalanuvchi
  if (import.meta.env.DEV) {
    return {
      id: 1467675358,
      first_name: 'Dev',
      last_name: 'User',
      username: 'dev_user',
      language_code: 'uz'
    };
  }
  
  // Production'da Telegram tashqarisida kirishga ruxsat yo'q
  return null;
}
App.tsx da getTelegramUser() null qaytarsa, foydalanuvchiga xabar ko'rsating: "Iltimos, ilovani Telegram orqali oching"

Xuddi shu mantiqni frontend/src/services/api.ts dagi getCachedUserProfile() va getDefaultUserProfile() funksiyalarida ham qo'llang

Backend web/dependencies/auth.py ni tekshiring — u yerda DEBUG fallback bor, lekin u settings.debug=True shartiga bog'langan (to'g'ri). Lekin settings.debug production'da false ekanligiga ishonch hosil qiling

Natija: Production'da faqat haqiqiy Telegram foydalanuvchilari kira oladi.

🔴 XATO #5: docker-compose.prod.yml — 3 ta servis yetishmaydi
Fayl: docker-compose.prod.yml (loyiha ildizida)

Muammo: Faqat bilimgo_web va bilimgo_bot xizmatlari bor. Quyidagilar YO'Q:

userbot (Pyrogram relay + assessment handler)

ai_worker (AI baholash workeri)

engagement_worker (Nudge xabarlari workeri)

Natija: Production'da AI baholash, nudge xabarlari va video relay ISHLAMAYDI.

Tuzatish:

docker-compose.prod.yml ni to'liq quyidagicha yangilang (yoki mavjud docker/docker-compose.yml ni asos qilib oling):

yaml
version: "3.8"

x-common: &common
  build:
    context: ./BilimGo
    dockerfile: docker/Dockerfile
  restart: always
  env_file:
    - ./BilimGo/.env
  volumes:
    - ./BilimGo/data:/app/data
    - ./BilimGo/logs:/app/logs
  networks:
    - bilimgo_net

services:
  bilimgo_web:
    <<: *common
    container_name: bilimgo_web
    ports:
      - "8000:8000"
    environment:
      - DB_PATH=/app/data/bilimgo.db
      - RELAY_INTERNAL_URL=http://bilimgo_userbot:8081
    depends_on:
      - bilimgo_userbot
    command: uvicorn web.main:app --host 0.0.0.0 --port 8000

  bilimgo_bot:
    <<: *common
    container_name: bilimgo_bot
    environment:
      - DB_PATH=/app/data/bilimgo.db
    command: python -m bot.main

  bilimgo_userbot:
    <<: *common
    container_name: bilimgo_userbot
    expose:
      - "8081"
    environment:
      - DB_PATH=/app/data/bilimgo.db
    command: python -m userbot.main

  bilimgo_ai_worker:
    <<: *common
    container_name: bilimgo_ai_worker
    environment:
      - DB_PATH=/app/data/bilimgo.db
    command: python -m workers.ai_evaluation_worker

  bilimgo_engagement_worker:
    <<: *common
    container_name: bilimgo_engagement_worker
    environment:
      - DB_PATH=/app/data/bilimgo.db
    command: python -m workers.engagement_monitor_worker

networks:
  bilimgo_net:
    driver: bridge
docker/docker-compose.yml ni tekshiring — u bilan mos bo'lishi kerak

.env fayli env_file orqali ulanadi (hardcoded env var'lar emas)

docker-compose -f docker-compose.prod.yml config bilan sintaksisni tekshiring

README yoki PROJECT_MEMORY.md da deploy qo'llanmasini yangilang

Natija: Production'da barcha 5 ta servis ishlaydi.

✅ YAKUNIY TEKSHIRUV (Har bir tuzatishdan keyin)
Quyidagi buyruqlarni ketma-ket ishga tushiring va natijalarni hisobot bering:

bash
# 1. Python sintaksis tekshiruvi
python -m py_compile BilimGo/services/ai_tutor_service.py
python -m py_compile BilimGo/web/routers/player.py

# 2. Hardcoded yo'llar qolmaganini tekshirish
grep -rn "Users/Acer" BilimGo/ frontend/ || echo "✅ Hardcoded yo'llar yo'q"
grep -rn "get_by_lesson_id" BilimGo/ || echo "✅ Noto'g'ri metod chaqiruvi yo'q"
grep -rn "gemini-3.7" frontend/ BilimGo/ || echo "✅ Noto'g'ri model yo'q"

# 3. Testlar
pytest BilimGo/tests/ -v

# 4. Frontend build
cd frontend && npm run build

# 5. Docker compose tekshiruvi
docker-compose -f docker-compose.prod.yml config
📋 HISOBOT FORMATI
Har bir xato uchun quyidagi formatda hisobot bering:

text
### XATO #N: <qisqa nom>
- Fayl: <fayl yo'li>
- O'zgargan qatorlar: <N>
- Nima o'zgardi: <qisqa tavsif>
- Test natijasi: ✅ PASS / ❌ FAIL
- Qo'shimcha izoh: <agar kerak bo'lsa>
🚫 NIMA QILMASLIK KERAK
❌ Boshqa fayllarga "yaxshilash" uchun tegmang — faqat ko'rsatilgan 5 ta xatoni tuzating

❌ Funksiyalar nomlarini o'zgartirmang (API shartnomasi buziladi)

❌ Yangi kutubxona qo'shmang — mavjudlari bilan tuzating

❌ .env faylini commit qilmang (u allaqachon .gitignoreda)

❌ Mock ma'lumotlarni o'chirmang — bu keyingi bosqichda alohida vazifa

🎯 YAKUNIY MAQSAD
5 ta kritik xato tuzatilgandan so'ng:

AI Ustoz ishlaydi (frontend + backend)

Docker/Linux serverda videolar ochiladi

Production'da faqat haqiqiy Telegram foydalanuvchilari kira oladi

Barcha 5 ta servis production'da ishlaydi

Boshlang! Har bir xatoni ketma-ket tuzatib, hisobot bering.

