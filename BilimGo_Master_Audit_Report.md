# 🏆 BilimGo Platformasi: 5 Subagent Bosh Audit Hisoboti (Master Audit Report)

> **Xulosa**: Ushbu audit 5 ta mustaqil va ixtisoslashtirilgan subagent tomonidan kod bazasiga hech qanday o'zgartirish kiritmasdan (**Read-Only** rejimida) o'tkazildi. Tahlil natijasida real prodakshenga chiqishdan oldin zudlik bilan hal etilishi shart bo'lgan **10 ta kritik xavfsizlik va barqarorlik muammolari**, **8 ta takrorlangan kod (DRY) bloklari** hamda **tizimli optimallashtirish yo'nalishlari** aniqlandi.

---

## 👥 Auditda Ishtirok Etgan Subagentlar va Ularning Yo'nalishlari
1. 🤖 **1-Subagent (Backend & Telegram Bot Auditor)**: Bot handlers, keyboards, middlewares, FSM states va bot oqimlari.
2. 🗄️ **2-Subagent (Database & Repositories Auditor)**: SQLite arxitekturasi, 30 ta repozitoriy, migratsiyalar va concurrency muammolari.
3. 💳 **3-Subagent (Business Logic & Payment Auditor)**: Payme, Click, to'lovlar, avto-debit, AI integratsiyasi va servislar.
4. 💻 **4-Subagent (Frontend & Telegram WebApp Auditor)**: React, Vite, WebApp SDK, interfeys himoyasi, mobil klaviatura va API bog'lanishlar.
5. 🛡️ **5-Subagent (Production Readiness, Security & Infra Auditor)**: Docker, env konfiguratsiyasi, CORS, WebSocket, portlar va xavfsizlik.

---

## 🚨 1. ENG KRITIK XATOLAR VA XAVFSIZLIK ZAIFLIKLARI (BLOCKERS)

Quyidagi xatolar platforma real serverga yuklanganda tizimning qulashiga yoki moliyaviy/xavfsizlik oqibatlariga olib keladi:

### 🔴 1.1. Payme Webhook Autentifikatsiyasi Yo'qligi (Bepul Kurs Xaridi)
- **Fayl**: [`BilimGo/web/routers/payments.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/web/routers/payments.py#L118-L136)
- **Muammo**: `/api/payments/payme` endpointida Payme'ning majburiy `Authorization: Basic ...` (Merchant ID va Secret Key) sarlavhasi tekshirilmaydi.
- **Oqibat**: Istalgan begona shaxs internet orqali oddiy JSON so'rov yuborib (`PerformTransaction`), xaridni 0 so'm to'lab `paid` holatiga o'tkaza oladi. Shuningdek, Payme sertifikatsiyasidan o'tish imkonsiz.

### 🔴 1.2. `DEBUG=true` Orqali Admin Huquqlarini Chetlab O'tish (Auth Bypass)
- **Fayl**: [`BilimGo/web/dependencies/auth.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/web/dependencies/auth.py#L50-L83)
- **Muammo**: Hozirda `DEBUG=true` bo'lgani sababli, sarlavhada `X-Telegram-User-Id: 1467675358` yuborgan har qanday begona odam tizim tomonidan Bosh Admin sifatida qabul qilinadi. Agar umuman sarlavha berilmasa ham tizim avtomatik admin hisoblanadi.

### 🔴 1.3. Bepul Kurs Ochib Berilishidagi Biznes Mantiq Xatosi
- **Fayl**: [`BilimGo/bot/handlers/common/_utils.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/bot/handlers/common/_utils.py#L181-L186)
- **Muammo**: Foydalanuvchi botga referal havola orqali kirgan zahoti unga `grant_course_access(..., granted_via_sale_id=0)` chaqirilib, kurs bepul ochib berilmoqda. To'lov tizimlari o'z ma'nosini yo'qotadi.

### 🔴 1.4. `admin_repo.py` dagi SQL Crash (`no such column: status`)
- **Fayl**: [`BilimGo/db/repositories/admin_repo.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/db/repositories/admin_repo.py#L12)
- **Muammo**: `sales` jadvalida ustun nomi `payment_status` bo'lishiga qaramay, so'rovda `WHERE status = 'paid'` yozilgan.
- **Oqibat**: Admin statistikani ochmoqchi bo'lganida admin panel darhol xatolik bilan qulaydi.

### 🔴 1.5. `cabinet_repo.py` dagi Maxfiylik Sizishi (Barcha Kabinetlar Hammaga Ochiq)
- **Fayl**: [`BilimGo/db/repositories/cabinet_repo.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/db/repositories/cabinet_repo.py#L94-L105)
- **Muammo**: `list_my_cabinets` metodida `LEFT JOIN` qilingan, lekin `WHERE cm.user_id = ?` sharti qo'yilmagan. Natijada har bir talaba va mentor platformadagi mutlaqo barcha xususiy kabinetlarni o'ziniki kabi ko'radi.

### 🔴 1.6. `ContentProtection.tsx` Mobil Klaviaturada Ekranni Qoraytirib Qo'yishi
- **Fayl**: [`frontend/src/components/ContentProtection.tsx`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/frontend/src/components/ContentProtection.tsx#L31-L45)
- **Muammo**: Mobil telefonda (iOS/Android) foydalanuvchi inputga bosib klaviaturani ochganda `window.blur` ishlaydi. Ilova buni "ekran yozish" deb o'ylab, butun ekranga `z-[99999]` qora parda tortib qo'yadi va videoni to'xtatadi. Talaba hech narsa yoza olmaydi.

### 🔴 1.7. `mentor_add.py` da Mavjud Bo'lmagan Metod (Silent AttributeError)
- **Fayl**: [`BilimGo/bot/handlers/common/mentor_add.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/bot/handlers/common/mentor_add.py#L201-L206)
- **Muammo**: `AccessGrantRepository` da `grant_access` metodi yo'q (`grant_course_access` mavjud). Xato `try/except Exception: pass` bilan yashirilgan. Natijada admin qo'shgan mentorga kurslar amalda ochilmaydi.

### 🔴 1.8. `user_repo.py` da Import Qilinmagan `NotFoundError`
- **Fayl**: [`BilimGo/db/repositories/user_repo.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/db/repositories/user_repo.py#L65-L68)
- **Muammo**: `NotFoundError` import qilinmagani sababli, foydalanuvchi topilmaganda toza xatolik o'rniga `NameError` ko'tarilib tizim qulaydi.

### 🔴 1.9. Mavjud Bo'lmagan AI Modeli (`claude-sonnet-5`)
- **Fayl**: [`BilimGo/core/config.py`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/BilimGo/core/config.py#L176)
- **Muammo**: Anthropic API da bunday model mavjud emas. Natijada AI Ustoz va talabalar vazifasini AI orqali tekshirish 100% 404 xatosi berib ishlamaydi.

### 🔴 1.10. `docker-compose.prod.yml` ning Ishga Yaroqsizligi
- **Fayl**: [`docker-compose.prod.yml`](file:///C:/Users/Acer/Downloads/BilimGo_TOLIQ/docker-compose.prod.yml#L1-L31)
- **Muammo**: Asosiy ishchi konteynerlar (`userbot`, `ai_worker`, `engagement_worker`) yo'q, shuningdek `.env` fayli yuklanmagan. Bot ishga tushishi bilanoq `_require("BOT_TOKEN")` RuntimeError tashlab to'xtaydi.

---

## ⚡ 2. MA'LUMOTLAR BAZASI VA CONCURRENCY MUAMMOLARI

1. **Yagona Connection va Tranzaksiya To'qnashuvi**:
   - `BilimGo/db/database.py` da butun dastur uchun bitta `self._conn` ishlatilgan. Bir vaqtda bir nechta asinxron so'rov tranzaksiyaga kirganda `OperationalError: cannot start a transaction within a transaction` kelib chiqadi.
2. **Repozitoriylardagi Premature Commit**:
   - Repozitoriy metodlarida `await self._conn.commit()` majburiy chaqirilgani sababli, tashqi servisdagi `transaction()` orqaga qaytara (rollback qila) olmaydi.
3. **Runtime DDL (`CREATE TABLE`)**:
   - `broadcast_repo.py` har safar xabar yuborishda `CREATE TABLE IF NOT EXISTS broadcasts` chaqiradi. Bu butun bazani schema-lock holatiga tushiradi.
4. **Ortiqcha Dublikat Indekslar**:
   - `users(telegram_id)`, `delivery_tokens(token_hash)` kabi ustunlarda `UNIQUE` constraint bo'la turib, yana alohida indekslar ochilgan. Bu yozish amallarini behuda sekinlashtiradi.

---

## 🔁 3. TAKRORLANGAN KODLAR (DRY BUZILISHLARI)

1. **`_build_payment_service()` Dublikati**:
   - `bot/handlers/student/purchase.py` va `web/routers/payments.py` da 20 qatorlik fabrika kodi aynan bir xil takrorlangan.
2. **`VideoPlayerView.tsx` da 60 Qatorlik JSX Dublikati**:
   - 441–501 va 724–785-qatorlarda matnli dars shabloni va nusxalash tugmasi ikki marta nusxalangan.
3. **Admin va Statistika Handlerlari Dublikati**:
   - `admin/broadcast.py` dagi 60+ qatorlik `@router.message(Command("admin"))` va statistika kodi `admin/statistics.py` da mavjud bo'lgani sababli mutlaqo o'lik (dead code) bo'lib qolgan.
4. **Tarqoq Telegram Xabar Yuborish Mantiqlari**:
   - `lesson_completion_service.py` va `admin_notifier.py` da `httpx.AsyncClient` orqali xabar yuborish alohida-alohida qayta yozilgan.
5. **Takroriy String va Vaqt Formatlash Funksiyalari**:
   - `live_session_service.py` va `live_session_repo.py` da `clean_id` logikasi 9 marta takrorlangan.
   - Frontendda `formatDuration` funksiyasi 4 ta alohida faylda qayta yozilgan.

---

## 🚀 4. REAL PRODAKSHENDA ULANMAY QOLADIGAN JOYLAR

1. **Frontend API URL o'qilmasligi**:
   - `frontend/src/services/api.ts` da `process.env.VITE_API_URL` yozilgan. Vite brauzerda buni o'qiy olmaydi (`import.meta.env` kerak). Natijada mobil telefonlarda so'rovlar `http://localhost:8000` ga ketib qulab qoladi.
2. **Insecure WebSocket (`ws://` vs `wss://`)**:
   - Telegram WebApp faqat HTTPS da ishlaydi. Jonli efirda shifrlanmagan `ws://` ochilishi tufayli brauzer xavfsizlik vajidan efir ulanishini bloklaydi.
3. **Click Token Auth 401 Xatosi**:
   - Karta bog'lash va avto-debitda Click v2 talab qiladigan SHA1 imzo o'rniga oddiy matn ketayotgani sababli prodakshenda barcha karta amallari `401 Unauthorized` qaytaradi.
4. **Hardcoded Windows Yo'llari**:
   - `player.py` da `C:/Users/Acer/...` yo'llari mavjud bo'lib, Linux/Docker serverlarida videolar topilmay qoladi.
5. **CORS Noto'g'ri Sozlamasi**:
   - `allow_origins=["*"]` va `allow_credentials=True` birga ishlatilgan. Brauzerlar bunday konfiguratsiyani xavfsizlik standarti bo'yicha bloklaydi.
6. **Telegram Polling vs Webhook**:
   - Bot faqat polling orqali ishlaydi va `MemoryStorage` ishlatadi. Server qayta yonganda talabalarning arizalari va to'lov holatlari o'chib ketadi.

---

## 🛠️ 5. YAXSHILASH BO'YICHA BOSQICHMA-BOSQICH REJA (ACTION PLAN)

### 1-Bosqich: Xavfsizlik va Kritik Buglarni Bartaraf Etish (1-kun)
1. `/api/payments/payme` ga Payme Basic Auth tekshiruvini kiritish.
2. `.env` da `DEBUG=false` ga o'tkazish va auth fallback orqali admin bo'lib olish tuynuklarini yopish.
3. `start.py` va `_utils.py` dagi tekin kurs berish mantiqini faqat to'lov tasdiqlangandan keyin ishlaydigan qilish.
4. `admin_repo.py` dagi `status` ni `payment_status` ga to'g'rilash.
5. `user_repo.py` ga `NotFoundError` importini qo'shish.
6. `mentor_add.py` dagi `grant_access` ni `grant_course_access` ga almashtirish.

### 2-Bosqich: Interfeys va WebApp Barqarorligi (2-kun)
1. `ContentProtection.tsx` dan `window.blur` ni olib tashlash, mobil klaviatura chiqqanda qora ekran bo'lishini to'xtatish.
2. `api.ts` dagi API manzilini `import.meta.env.VITE_API_URL` va nisbiy manzilga o'tkazish.
3. Jonli efir WebSocket'ini faqat `wss://` orqali ochish.
4. Demo foydalanuvchini faqat dev rejimda ishlatish.

### 3-Bosqich: Baza va Infratuzilmani To'g'rilash (3-kun)
1. `cabinet_repo.py` dagi `list_my_cabinets` so'roviga `WHERE cm.user_id = ?` qo'shib, begona kabinetlarni yashirish.
2. `docker-compose.prod.yml` ga qolgan 3 ta servisni qo'shish va `.env` faylini ulash.
3. `config.py` dagi Anthropic model nomini `claude-3-5-sonnet-20241022` ga to'g'rilash.
4. Takrorlangan kodlarni umumiy utility va servislarga jamlash.
