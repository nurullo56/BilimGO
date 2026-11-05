# 🚀 BilimGo Loyihasida Bajarilgan O'zgarishlar va Tuzatishlar (Changelog)

Ushbu hujjat BilimGo platformasini tahlil qilish natijasida aniqlangan kritik nuqsonlar, runtime xatolar, xavfsizlik zaifliklari va Clean Architecture nomuvofiqliklarini bartaraf etish bo'yicha amalga oshirilgan barcha o'zgarishlarni o'z ichiga oladi.

---

## 📌 Qisqacha Xulosa

Barcha o'zgarishlar 4 ta ketma-ket bosqichda amalga oshirildi:
1. **1-bosqich: Data / DB Qatlami** (SQL migratsiyalar yaxlitligi, tranzaksiyalar xavfsizligi, SQL parametrizatsiya)
2. **2-bosqich: Telegram Bot Qatlami** (Runtime `NameError` crashni tuzatish, shadowed handlerlarni tozalash, FloodWait himoyasi)
3. **3-bosqich: Biznes Servislar Qatlami** (Adaptiv kunlik limitni ulash, matn shablonlari formati, `create_default` factory metodlari)
4. **4-bosqich: Web API va Xavfsizlik** (WebSocket HMAC SHA-256 InitData avtentifikatsiyasi, CORS siyosati to'g'rilanishi)

---

## 🗄️ 1-Bosqich: Data / DB Qatlami

### 1. `0026_broadcasts_and_course_waitlist.sql` (Yangi Rasmiy Migratsiya)
- **Fayl:** `BilimGo/db/migrations/0026_broadcasts_and_course_waitlist.sql`
- **Muammo:** 
  - `access_grant_repo.py:get_student_courses_with_progress` so'rovida `courses.is_waitlist` ustuni chaqirilgan, biroq `0001`–`0025` migratsiyalarining birortasida bu ustun yo'q edi. Yangi muhitda tizim `OperationalError: no such column: c.is_waitlist` xatosi bilan qulardi.
  - `broadcast_repo.py` ichida har safar xabar yuborishda runtime da `CREATE TABLE IF NOT EXISTS broadcasts ...` bajarilar edi.
- **Yechim:** 
  - Yangi `0026` migratsiya fayli yaratildi va `broadcasts` jadvali hamda `courses.is_waitlist` ustuni rasmiy migratsiya zanjiriga kiritildi.

### 2. `database.py` (Migratsiya Chidamliligi)
- **Fayl:** `BilimGo/db/database.py`
- **Yechim:** Agar mavjud bazalarda `is_waitlist` ustuni allaqachon mavjud bo'lsa, SQLite `duplicate column name` xatosini tashlamasdan, migratsiyani xavfsiz o'tkazib `schema_migrations` ga yozib qo'yuvchi chidamli himoya kiritildi.

### 3. `license_node_repo.py` (Unutilgan Commit)
- **Fayl:** `BilimGo/db/repositories/license_node_repo.py`
- **Muammo:** `update_course_id` metodida `await self._conn.commit()` chaqirilmagan, o'zgarishlar bazaga saqlanmay qolishi mumkin edi.
- **Yechim:** `await self._conn.commit()` qo'shildi.

### 4. `broadcast_repo.py` (Runtime DDL Tozalash)
- **Fayl:** `BilimGo/db/repositories/broadcast_repo.py`
- **Yechim:** `create_broadcast` metodidan runtime DDL (`CREATE TABLE IF NOT EXISTS`) olib tashlanib, faqat toza `INSERT` so'rovi qoldirildi.

### 5. `lesson_view_repo.py` (Xavfsiz Parametrli SQL)
- **Fayl:** `BilimGo/db/repositories/lesson_view_repo.py`
- **Muammo:** `get_daily_activity_map` metodida `days` parametri f-string orqali SQL ga to'g'ridan-to'g'ri joylashtirilgan edi.
- **Yechim:** `datetime('now', '-' || ? || ' days')` parametrli SQLite so'roviga o'tkazildi.

---

## 🤖 2-Bosqich: Telegram Bot Qatlami

### 1. `student/catalog.py` (Kritik Runtime Crash Tuzatildi)
- **Fayl:** `BilimGo/bot/handlers/student/catalog.py`
- **Muammo:** `handle_waitlist_leave` callback handlerida `count` o'zgaruvchisi e'lon qilinmasdan `f"Hozircha: {count} kishi navbatda turibdi"` shabloniga qo'yilgan edi. Talaba navbatdan chiqqanda bot `NameError: name 'count' is not defined` xatosi bilan qulardi.
- **Yechim:** `res = await course_service.leave_waitlist(...)` natijasidan `count = res.get("waitlist_count", 0)` va `course_title = res.get("course_title", "Kurs")` xavfsiz olinishi ta'minlandi.

### 2. `admin/broadcast.py` (Shadowed Handler Tozalandi)
- **Fayl:** `BilimGo/bot/handlers/admin/broadcast.py`
- **Muammo:** `statistics.py` tomonidan oldinroq ro'yxatdan o'tkazilgani sababli hech qachon ishlamaydigan o'lik `handle_admin_command` kodi olib tashlandi.

### 3. `admin/statistics.py` (Takroriy Log Chaqiruvi)
- **Fayl:** `BilimGo/bot/handlers/admin/statistics.py`
- **Yechim:** Ketma-ket ikki marta takrorlangan `logger.info("Admin buyrug'i chaqirildi...")` satrining bittasi tozalandi.

### 4. `mentor/live.py` (FloodWait Himoyasi)
- **Fayl:** `BilimGo/bot/handlers/mentor/live.py`
- **Muammo:** Jonli dars xabarnomasini yuzlab talabalarga ketma-ket yuborishda Telegram `429 Too Many Requests (FloodWait)` chekloviga tushish xavfi bor edi.
- **Yechim:** `import asyncio` kiritilib, xabarlar yuborish tsikliga `await asyncio.sleep(0.05)` va xatoliklarni xavfsiz tutuvchi blok qo'shildi.

---

## ⚙️ 3-Bosqich: Biznes Servislar Qatlami

### 1. `access_control_service.py` (Adaptive Unlock Tekshiruvi)
- **Fayl:** `BilimGo/services/access_control_service.py`
- **Muammo:** `AdaptiveUnlockService` konstruktorga kiritilgan, biroq `ensure_can_watch` metodida undan foydalanilmagan edi. Natijada kunlik adaptiv dars ochish limiti ishlamasdan qolgan.
- **Yechim:** Talaba dars ko'rmoqchi bo'lganda uning kunlik limitingizdan oshmaganligi (`lesson.order_index <= limit`) tekshirilishi faollashtirildi. Clean Architecture talabiga muvofiq `create_default(cls, conn=None)` zavod metodi qo'shildi.

### 2. `engagement_monitor_service.py` (Nudge Xabar Shablonlari)
- **Fayl:** `BilimGo/services/engagement_monitor_service.py`
- **Muammo:** `NUDGE_STEPS` shablonlarida `"Salom{name}!"` format parametri bor edi, lekin unga qiymat berilmasdan xom holda yuborilar edi.
- **Yechim:** Shablonlar toza va tabiiy o'zbek tiliga keltirildi (`"Salom! ..."`), `create_default(cls, conn=None)` metodi qo'shildi.

### 3. `broadcast_service.py` (Takroriy Return)
- **Fayl:** `BilimGo/services/broadcast_service.py`
- **Yechim:** 71- va 73-qatorlardagi ortiqcha takroriy `return []` qatoridan biri olib tashlandi.

---

## 🌐 4-Bosqich: Web API va Xavfsizlik

### 1. `live_websocket.py` (WebSocket Avtentifikatsiyasi)
- **Fayl:** `BilimGo/web/routers/live_websocket.py`
- **Muammo:** Jonli efir WebSocket endpointi ochiq `?user_id=123` parametri orqali hech qanday tekshiruvsiz ulanishga ruxsat berardi. Begona shaxslar ixtiyoriy ID bilan efirga kira olardi.
- **Yechim:** Telegram WebApp HMAC SHA-256 `init_data` token tekshiruvi joriy qilindi. Ruxsatsiz yoki soxta ma'lumotlar bilan ulanishlar `4001: Authentication required` kodi bilan darhol yopiladi (mahalliy testlar uchun DEBUG moslashuvchanligi saqlab qolindi).

### 2. `web/main.py` (CORS Xavfsizligi)
- **Fayl:** `BilimGo/web/main.py`
- **Muammo:** `allow_origins=["*"]` bilan `allow_credentials=True` birgalikda qo'llanilgan, bu W3C CORS xavfsizlik spetsifikatsiyasiga zid edi.
- **Yechim:** Aniq ruxsat etilgan mahalliy domenlar (`localhost:3000`, `localhost:5173`), `settings.webapp.base_url` hamda `https://*.telegram.org` regexi xavfsiz tarzda o'rnatildi.

---

## 🧪 Sinov va Verifikatsiya Natijalari

1. **Sintaksis va Kompilyatsiya (`py_compile`):**
   - O'zgartirilgan barcha 11 ta fayl xatoliksiz kompilyatsiya qilindi.
2. **Avtomatlashtirilgan Unit Testlar (`pytest`):**
   - Barcha **10 ta unit test 100% muvaffaqiyatli o'tdi**:
   ```text
   BilimGo\tests\test_analytics_clean_refactor.py PASSED  [ 10%]
   BilimGo\tests\test_cabinet_clean_refactor.py PASSED    [ 20%]
   BilimGo\tests\test_chat_clean_refactor.py PASSED       [ 30%]
   BilimGo\tests\test_services.py PASSED (5 ta test)      [ 80%]
   BilimGo\tests\test_users_clean_refactor.py PASSED      [100%]
   ============================= 10 passed in 5.07s ==============================
   ```
3. **Matn Kodlanishi:**
   - 100% toza UTF-8 va haqiqiy Unicode emojilar (📦, 🤖, 🎯, 💾, 🛑, ✅), bitta ham Mojibake (`рџ...`) yo'q.
