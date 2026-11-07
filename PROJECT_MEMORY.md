# 🧠 Loyiha Xotirasi: BilimGo_TOLIQ

> [!NOTE]
> Ushbu fayl AGY (Antigravity) uchun loyihaning to'liq, chuqur va batafsil kontekst xaritasidir. 
> AGY har safar barcha fayllarni qayta titkilamasdan, shu xarita orqali loyihaning arxitekturasi, har bir qatlami, har bir fayli va ularning aniq vazifalarini darhol tushunadi.

---

## 📌 Umumiy Ma'lumot
- **Loyiha nomi**: `BilimGo_TOLIQ`
- **Loyiha turi**: EdTech Platform / Edu-LMS (Telegram Bot, Telegram Mini App Web SPA, FastAPI REST API, Pyrogram Userbot Relay Streaming, Background Workers)
- **Ildiz yo'li**: `C:\Users\Acer\Downloads\BilimGo_TOLIQ`
- **Asosiy texnologiyalar**: 
  - **Backend**: Python 3.11+, FastAPI, Aiogram 3, Pyrogram, Aiohttp, SQLite (`aiosqlite` WAL mode)
  - **Frontend**: React 18, Vite, TypeScript, TailwindCSS, WebRTC
  - **AI & Integratsiyalar**: Google Gemini 2.0 Flash, Anthropic Claude, Click API, Payme Merchant API, Cloudflare Tunnel

---

## 📁 Loyiha Tuzilmasi (Daraxt)

```text
BilimGo_TOLIQ/
├── BilimGo/
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── admin/
│   │   │   │   ├── broadcast.py
│   │   │   │   ├── course_waitlist.py
│   │   │   │   ├── mentor_approval.py
│   │   │   │   ├── quota.py
│   │   │   │   └── statistics.py
│   │   │   ├── common/
│   │   │   │   ├── cabinet_link.py
│   │   │   │   ├── mentor_add.py
│   │   │   │   ├── profile.py
│   │   │   │   ├── start.py
│   │   │   │   └── _utils.py
│   │   │   ├── mentor/
│   │   │   │   ├── broadcast.py
│   │   │   │   ├── cabinet.py
│   │   │   │   └── live.py
│   │   │   └── student/
│   │   │       ├── catalog.py
│   │   │       ├── progress.py
│   │   │       └── purchase.py
│   │   ├── keyboards/
│   │   │   ├── admin/
│   │   │   │   ├── broadcast_kb.py
│   │   │   │   ├── menu_kb.py
│   │   │   │   └── quota_kb.py
│   │   │   ├── common/
│   │   │   │   ├── cabinet_kb.py
│   │   │   │   ├── mentor_assign_kb.py
│   │   │   │   ├── onboarding_kb.py
│   │   │   │   └── profile_kb.py
│   │   │   ├── mentor/
│   │   │   │   ├── broadcast_kb.py
│   │   │   │   ├── live_kb.py
│   │   │   │   └── menu_kb.py
│   │   │   └── student/
│   │   │       ├── catalog_kb.py
│   │   │       ├── menu_kb.py
│   │   │       └── payment_kb.py
│   │   ├── middlewares/
│   │   │   ├── antiflood.py
│   │   │   └── auth.py
│   │   ├── states/
│   │   │   └── fsm_states.py
│   │   └── main.py
│   ├── core/
│   │   ├── cache.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── migrations/
│   │   │   ├── 0001_init_users.sql
│   │   │   ├── ... (0001 dan 0026 gacha)
│   │   │   └── 0026_broadcasts_and_course_waitlist.sql
│   │   ├── repositories/
│   │   │   ├── access_grant_repo.py
│   │   │   ├── admin_repo.py
│   │   │   ├── ai_token_repo.py
│   │   │   ├── assessment_criteria_repo.py
│   │   │   ├── base.py
│   │   │   ├── broadcast_repo.py
│   │   │   ├── cabinet_repo.py
│   │   │   ├── chat_repo.py
│   │   │   ├── click_transaction_repo.py
│   │   │   ├── completion_notification_repo.py
│   │   │   ├── comprehension_check_repo.py
│   │   │   ├── course_repo.py
│   │   │   ├── course_tariff_repo.py
│   │   │   ├── daily_unlock_plan_repo.py
│   │   │   ├── delivery_token_repo.py
│   │   │   ├── engagement_repo.py
│   │   │   ├── lesson_repo.py
│   │   │   ├── lesson_view_repo.py
│   │   │   ├── license_node_repo.py
│   │   │   ├── live_session_repo.py
│   │   │   ├── mentor_application_repo.py
│   │   │   ├── mentor_card_repo.py
│   │   │   ├── mentor_userbot_repo.py
│   │   │   ├── payme_transaction_repo.py
│   │   │   ├── quiz_repo.py
│   │   │   ├── royalty_repo.py
│   │   │   ├── sale_repo.py
│   │   │   ├── server_expense_repo.py
│   │   │   ├── tariff_quota_repo.py
│   │   │   ├── unlock_tier_repo.py
│   │   │   └── user_repo.py
│   │   └── database.py
│   ├── services/
│   │   ├── access_control_service.py
│   │   ├── adaptive_unlock_service.py
│   │   ├── admin_notifier.py
│   │   ├── ai_evaluation_service.py
│   │   ├── ai_tutor_service.py
│   │   ├── analytics_service.py
│   │   ├── auto_debit_service.py
│   │   ├── broadcast_service.py
│   │   ├── cabinet_service.py
│   │   ├── click_service.py
│   │   ├── cohort_service.py
│   │   ├── course_service.py
│   │   ├── delivery_token_service.py
│   │   ├── engagement_monitor_service.py
│   │   ├── lesson_completion_service.py
│   │   ├── live_session_service.py
│   │   ├── live_stream_service.py
│   │   ├── messaging_service.py
│   │   ├── payme_service.py
│   │   ├── payment_service.py
│   │   ├── quiz_service.py
│   │   ├── royalty_service.py
│   │   └── user_service.py
│   ├── userbot/
│   │   ├── assessment_handler.py
│   │   ├── channel_commands.py
│   │   ├── relay_server.py
│   │   └── main.py
│   ├── web/
│   │   ├── dependencies/
│   │   │   └── auth.py
│   │   ├── routers/
│   │   │   ├── admin_analytics.py
│   │   │   ├── ai_tutor.py
│   │   │   ├── cabinet.py
│   │   │   ├── cards.py
│   │   │   ├── chat.py
│   │   │   ├── feedback.py
│   │   │   ├── live.py
│   │   │   ├── live_websocket.py
│   │   │   ├── notifications.py
│   │   │   ├── payments.py
│   │   │   ├── player.py
│   │   │   ├── quiz.py
│   │   │   ├── server_expenses.py
│   │   │   ├── users.py
│   │   │   └── waitlist.py
│   │   └── main.py
│   └── workers/
│       ├── ai_evaluation_worker.py
│       └── engagement_monitor_worker.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdminDashboardView.tsx
│   │   │   ├── ApiSettingsModal.tsx
│   │   │   ├── BottomTabBar.tsx
│   │   │   ├── CabinetChatView.tsx
│   │   │   ├── CardBindingModal.tsx
│   │   │   ├── CatalogView.tsx
│   │   │   ├── ContentProtection.tsx
│   │   │   ├── CourseDetailView.tsx
│   │   │   ├── FeedbackModal.tsx
│   │   │   ├── LessonAiAssistant.tsx
│   │   │   ├── LessonQuizCard.tsx
│   │   │   ├── LiveSessionsView.tsx
│   │   │   ├── LiveStreamView.tsx
│   │   │   ├── MentorStatsView.tsx
│   │   │   ├── MyCoursesView.tsx
│   │   │   ├── Navbar.tsx
│   │   │   ├── NotificationsModal.tsx
│   │   │   ├── PaymentModal.tsx
│   │   │   ├── ProfileView.tsx
│   │   │   ├── RichAiContent.tsx
│   │   │   ├── TgEmoji.tsx
│   │   │   ├── TgEmojiPicker.tsx
│   │   │   ├── VideoPlayerView.tsx
│   │   │   └── VoiceReportModal.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── telegram.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── types.ts
├── run_all.py
├── restart.py
├── sync_courses.py
├── docker-compose.yml
└── .env
```

---

## 🏛️ Clean Architecture va Qatlamlar Ajratilishi (QAT'IY QOIDA)

Ushbu loyihada qat'iy ravishda **Clean Architecture** va **Separation of Concerns (SoC)** tamoyillariga amal qilinadi. Yangi funksiya yozishda yoki mavjud kodni o'zgartirishda quyidagi qoidalardan chetga chiqish QAT'IYAN TAQIQLANADI:

### 1. Qatlamlar Taqsimoti va Majburiyatlari:

1. **Repozitoriylar (`BilimGo/db/repositories/`) — Ma'lumotlar Bazasi Qatlami:**
   - Barcha xom SQL so'rovlari (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, tranzaksiyalar) **FAQAT va FAQAT** shu qatlamda bo'ladi.
   - Har bir repozitoriy o'z domeniga tegishli jadval bilan ishlaydi va natijani toza model (dataclass) yoki ma'lumotlar to'plami (dict/list) shaklida qaytaradi.

2. **Servislar (`BilimGo/services/`) — Biznes Mantiq Qatlami:**
   - Barcha biznes qoidalar, tekshiruvlar, hisob-kitoblar, limitlar, muddatlar va bir nechta repozitoriylarni muvofiqlashtirish shu yerda bajariladi.
   - 🛑 **QAT'IY TAQIQ:** Servislar ichida to'g'ridan-to'g'ri `conn.execute(...)`, `SELECT ...`, `UPDATE ...` kabi xom SQL yozish 100% taqiqlanadi! Har qanday DB amali tegishli repozitoriy metodi orqali bajarilishi shart.
   - Har bir servisda markazlashgan `create_default(cls, conn=None)` zavod (factory) metodi bo'lishi shart.

3. **Routerlar (`BilimGo/web/routers/`) — Web / HTTP Qatlami:**
   - Routerlar faqat "Yupqa Controller" (Thin Controller) vazifasini bajaradi: HTTP parametrlarini tekshirish (Pydantic validation), kerakli servisni chaqirish va javob qaytarish (3-5 qatordan oshmasligi kerak).
   - 🛑 **QAT'IY TAQIQ:** Routerlar ichida xom SQL yozish, `database.conn` dan foydalanish yoki to'g'ridan-to'g'ri repozitoriy bilan murakkab biznes amallarini bajarish 100% taqiqlanadi! Barchasi `Depends(Service.create_default)` orqali servisga topshiriladi.

4. **Bot Handlerlar (`BilimGo/bot/handlers/`) — Telegram Foydalanuvchi Qatlami:**
   - Faqat Telegram xabarlarini qabul qilish, inline klaviaturalarni ko'rsatish va FSM holatlarini boshqarish.
   - 🛑 **QAT'IY TAQIQ:** Handlerlar ichida xom SQL yozilmaydi, biznes amallar servislar orqali amalga oshiriladi.

---

### 2. Yangi Imkoniyat Qo'shishning Qat'iy Ketma-ketligi (3 Qadam):

Har qanday yangi funksiya yoki endpoint quyidagi ketma-ketlikda yoziladi:
1. **1-qadam (DB):** Kerakli SQL so'rovni `db/repositories/` dagi tegishli faylga metod qilib qo'shish.
2. **2-qadam (Logika):** `services/` dagi tegishli servisga repozitoriyni chaqiruvchi va biznes mantiqni bajaruvchi metod yozish.
3. **3-qadam (Taqdimot):** `web/routers/` yoki `bot/handlers/` da ushbu servis metodini qisqagina chaqirib qo'yish.

---

## ⚙️ Asosiy Modullar va Har Bir Faylning Aniq Vazifalari

---

### 1. 🤖 Telegram Bot Qatlami (`BilimGo/bot/`)

- 📄 `bot/main.py` — Botning asosiy kirish nuqtasi (entrypoint). Aiogram Bot va Dispatcherni ishga tushiradi, FSM xotirasini sozlaydi, `AntiFloodMiddleware` va `AuthMiddleware` middleware'larini ulaydi, barcha admin, mentor, student va umumiy routerlarni ro'yxatdan o'tkazadi; `on_startup` va `on_shutdown` orqali adminlarga holat xabarnomalarini yuboradi, DB ulanishi va migratsiyalarini boshqarib, polling rejimida ishlaydi.
- 📄 `bot/middlewares/antiflood.py` — Spam va flood hujumlaridan himoya qiluvchi Aiogram middleware'i. Foydalanuvchilarning ketma-ket so'rovlari oralig'ini tekshiradi (minimal chegara: 0.8s), spam holatida xabarni bloklaydi va ogohlantiradi; xotira tozalash (`_cleanup_old_records`) mexanizmiga ega; adminlar uchun cheklov qo'llanmaydi.
- 📄 `bot/middlewares/auth.py` — Foydalanuvchilarni autentifikatsiya qilish va rolni boshqarish middleware'i. Har bir update kelganda `UserRepository` orqali foydalanuvchini topadi yoki yangi yaratadi; agar foydalanuvchi `ADMIN_IDS` ro'yxatida bo'lsa, avtomatik `admin` roliga ko'taradi va topilgan `user` obyektini barcha handlerlarga (`data["user"]`) uzatadi.
- 📄 `bot/states/fsm_states.py` — FSM (Finite State Machine) holatlar guruhlari to'plami. `ScheduleLiveStates` (jonli efir belgilash), `BroadcastStates` (admin tarqatmasi), `MentorBroadcastStates` (mentor shogirdlariga xabar tarqatishi), va `AddQuotaStates` (mentorga bepul dostup kvotasini qo'shish) holatlarini o'z ichiga oladi.

#### Bot Handlerlari:
- 📄 `bot/handlers/admin/broadcast.py` — Adminlar uchun keng qamrovli xabar tarqatish (Broadcast) handleri. `/broadcast`, `/admin_send`, `/send`, `/xabar` buyruqlari va callbacklar orqali barcha foydalanuvchilar, barcha mentorlar, alohida mentor shogirdlari yoki kurs talabalariga matn, rasm, video va audio xabarlarni jonli progress-bar monitoringi bilan ommaviy yuborishni amalga oshiradi.
- 📄 `bot/handlers/admin/course_waitlist.py` — Kurslarning Waitlist (kutish ro'yxati) va e'lonlarini boshqarish handleri. `/waitlist`, `/course_waitlist`, `/set_notice`, `/set_image` buyruqlari va inline tugmalar orqali kurslarni sotuv yoki navbat rejimiga o'tkazish, kurslar uchun e'lon matnlari va banner rasmlarini yangilash imkonini beradi.
- 📄 `bot/handlers/admin/mentor_approval.py` — Mentor arizalari va to'lov cheklarini tasdiqlash/rad etish handleri. Guruh mavzulari (Topic 2 va Topic 4) orqali mentorlik arizalarini ko'rib chiqish, rad etish/ma'qullash, nomzodga karta ma'lumotlarini yuborish, nomzod yuborgan to'lov chekini (`F.photo`) qabul qilish hamda to'lov tasdiqlanganda mentorga barcha kurslarni to'liq ochib berish logikasini bajaradi.
- 📄 `bot/handlers/admin/quota.py` — Mentorlarning 15 kunlik sinov davri bepul o'quvchi limitlarini boshqarish handleri. `/addquota`, `/limit`, `/quotas` buyruqlari orqali quyi mentorlar va kurslarni tanlab, tezkor (+5, +10, +20, +50, +100) yoki ixtiyoriy miqdorda kvota ajratadi va bu haqda mentorga darhol bildirishnoma jo'natadi.
- 📄 `bot/handlers/admin/statistics.py` — Admin boshqaruv paneli va umumiy platforma statistikasi handleri. `/admin` buyrug'i orqali admin boshqaruv markazini ko'rsatadi, "📊 Platforma statistikasi" tugmasi orqali jami foydalanuvchilar, jami mentorlar va har bir kurs bo'yicha talabalar soni hisobotini shakllantiradi.
- 📄 `bot/handlers/common/cabinet_link.py` — Foydalanuvchi biriktirilgan kabinet va guruh chatlarini ko'rsatish handleri. "💬 Kabinet va chat" menyusi orqali foydalanuvchi a'zo bo'lgan maxsus guruh chatlari va Mini App umumiy kabinet tugmalarini taqdim etadi.
- 📄 `bot/handlers/common/mentor_add.py` — Super Admin tomonidan yangi mentor tayinlash handleri. `/newmentor`, `/addmentor` orqali nomzodning Telegram ID raqamini qabul qiladi, asosiy kurs yo'nalishi va limit tarif paketini tanlab, unga litsenziya tuguni (node), kabinet va barcha mavjud kurslarni to'liq ochib beradi hamda `/mentors` buyrug'i orqali barcha mentorlar ro'yxatini chiqaradi.
- 📄 `bot/handlers/common/profile.py` — Foydalanuvchi profili va sotuv havolalari handleri. `/profile` buyrug'i orqali foydalanuvchi ma'lumotlari (ism, ID, telefon, rol) va Mini App havolasini ko'rsatadi; `/links` va `/courses` buyruqlari orqali mentorlar uchun Click/Payme online sotuv havolalari, lichkada to'laganlar uchun to'g'ridan-to'g'ri ochiq havolalar va umumiy kabinet taklif havolalarini taqdim etadi.
- 📄 `bot/handlers/common/start.py` — Botning markaziy ro'yxatdan o'tish va yo'naltirish handleri. `/start` buyrug'i va `F.contact` orqali foydalanuvchini ro'yxatga oladi, telefon raqamini profilga ulaydi, kirish payload parametrlarini (referal node, konkurs, to'g'ridan-to'g'ri kirish) tahlil qiladi, foydalanuvchini tegishli mentor kabinetiga biriktiradi va rolga mos asosiy menyuni chiqaradi.
- 📄 `bot/handlers/common/_utils.py` — Bot handlerlari uchun umumiy yordamchi funksiyalar (xabarlarni formatlash, rolni tekshirish).
- 📄 `bot/handlers/mentor/broadcast.py` — Mentorning o'z shogirdlariga xabar tarqatish handleri. `/mentor_broadcast` yoki "📢 Shogirdlarimga xabar" buyrug'i orqali mentorning barcha shogirdlariga yoki faqat ma'lum bir kurs o'quvchilariga matn, media va fayl xabarlarini jonli progress holati bilan yuboradi.
- 📄 `bot/handlers/mentor/cabinet.py` — Mentorning shaxsiy kabineti va moliyaviy-texnik monitoring handleri. "👥 Mening talabalarim" (talabalar ro'yxati), "📊 Statistika" (15 kunlik limit qoldig'i, AI tyutor va server/video infratuzilma xarajatlari, talabalar faolligi), "🔗 Kurslarim sotuv havolalari" va "💳 Ulangan karta (Avto-to'lov)" holati (royalti va avto-yechish ma'lumotlari)ni taqdim etadi.
- 📄 `bot/handlers/mentor/live.py` — Mentor jonli efirlari (Live stream) handleri. "🔴 Live dars belgilash" buyrug'i orqali kurs tanlash, efir sanasi va vaqtini kiritish, jonli efir xonasini yaratish, talabalarga efir boshlanishi haqida xabarnoma jo'natish (`live_notify`) va sessiyani bekor qilish imkoniyatini beradi.
- 📄 `bot/handlers/student/catalog.py` — Kurslar katalogi va kutish ro'yxati (Waitlist) handleri. "📚 Kurslar katalogi" orqali kurslar ro'yxatini chiqaradi; sotuvdagi kurslar uchun narx va xarid qilish tugmalarini, tayyorlanayotgan kurslar uchun esa navbatga yozilish (`waitlist:join`) va navbatdan chiqish (`waitlist:leave`) logikasini ta'minlaydi.
- 📄 `bot/handlers/student/progress.py` — Talabaning o'quv jarayoni va xarid qilingan kurslari handleri. "🎓 Mening kurslarim" menyusi orqali talaba ega bo'lgan faol kurslar ro'yxatini va Mini App ichida darslarni davom ettirish tugmalarini chiqaradi.
- 📄 `bot/handlers/student/purchase.py` — Talabalar uchun to'lov checkout handleri. Kurs tafsilotlaridan to'lov bosilganda Click yoki Payme provayderini aniqlaydi, `PaymentService.initiate_purchase` orqali to'lov yozuvini yaratadi va foydalanuvchiga to'lov qilish havolasini taqdim etadi.

#### Bot Klaviaturalari:
- 📄 `bot/keyboards/admin/broadcast_kb.py` — Admin ommaviy tarqatmasi uchun auditoriya tanlash va tasdiqlash inline klaviaturalari.
- 📄 `bot/keyboards/admin/menu_kb.py` — Admin boshqaruv markazining Reply va Inline bosh menyu tugmalari.
- 📄 `bot/keyboards/admin/quota_kb.py` — Mentorga tezkor va maxsus bepul dostup kvotalarini biriktirish inline klaviaturalari.
- 📄 `bot/keyboards/common/cabinet_kb.py` — Kabinetlar va guruh chatlariga o'tish tugmalari.
- 📄 `bot/keyboards/common/mentor_assign_kb.py` — Yangi mentor tayinlashda kurslar va tarif paketlarini tanlash tugmalari.
- 📄 `bot/keyboards/common/onboarding_kb.py` — Botga ilk bor kirganda telefon raqamini yuborish (`Request Contact`) tugmasi.
- 📄 `bot/keyboards/common/profile_kb.py` — Profil ko'rinishi, Mini App ochish va sotuv havolalari inline tugmalari.
- 📄 `bot/keyboards/mentor/broadcast_kb.py` — Mentorning o'z shogirdlariga xabar yuborishida kurs va guruh tanlash klaviaturalari.
- 📄 `bot/keyboards/mentor/live_kb.py` — Jonli efir belgilash, vaqt tanlash va boshlash/bekor qilish klaviaturalari.
- 📄 `bot/keyboards/mentor/menu_kb.py` — Mentor shaxsiy kabinetining Reply va Inline menyulari.
- 📄 `bot/keyboards/student/catalog_kb.py` — Kurslar katalogi, tariflar, waitlist va to'lovga o'tish tugmalari.
- 📄 `bot/keyboards/student/menu_kb.py` — Talabalar uchun "Katalog", "Kurslarim", "Profil" asosiy menyu tugmalari.
- 📄 `bot/keyboards/student/payment_kb.py` — To'lov usullari (Click / Payme) va to'lov sahifasiga o'tish tugmalari.

---

### 2. 💻 Userbot va Video Relay Streaming Qatlami (`BilimGo/userbot/`)

- 📄 `userbot/main.py` — Pyrogram Userbot va Relay serverining asosiy ishga tushirish fayli (entrypoint). Pyrogram Client'ni ishga tushiradi, baholash (`assessment_handler`) va kanal boshqaruvi (`channel_commands`) handlerlarini bog'laydi, Aiohttp asosidagi Relay HTTP serverini yoqadi va uzluksiz ishlashini ta'minlaydi.
- 📄 `userbot/relay_server.py` — Telegram yopiq kanallaridagi video va mediani mahalliy diskda saqlamasdan to'g'ridan-to'g'ri Mini Appga uzatuvchi (Zero-Storage Streaming) Aiohttp serveri. `/meta` (video/fayl hajmini aniqlash), `/relay` (chunklar bo'yicha uzluksiz oqimli HTTP Range video streaming) va `/send_message` (userbot nomidan xabar yuborish) endpointlariga ega bo'lib, `X-Internal-Secret` orqali xavfsiz autentifikatsiyani amalga oshiradi.
- 📄 `userbot/assessment_handler.py` — Talabalarning darslarni tushunish darajasini (Comprehension Check) qabul qilish handleri. Mentor tomonidan `/baholash <lesson_id>` yuborilganda chat kontekstini eslab qoladi; talaba shaxsiy chatda javob yozganda uning javobini `comprehension_checks` jadvaliga yozib, AI tahliliga uzatadi.
- 📄 `userbot/channel_commands.py` — Telegram kanallari bilan ishlash va darslarni avtomatlashtirilgan holda LMS bazasiga yuklash komandalari handleri. `.setchannel` (kanalni kuzatuvga olish), `.buildcourse` (kanaldagi video/audio/postlarni tahlil qilib tartibli darslar sifatida bazaga kiritish), `.courses` (mavjud kurslar va darslar soni), `.stats` (tizim statistikasi) va `.help` buyruqlarini boshqaradi.

---

### 3. 💾 Ma'lumotlar Bazasi va Migratsiyalar (`BilimGo/db/`)

- 📄 `db/database.py` — Yagona markazlashgan `aiosqlite` ulanish qatlami.
  - **Rejimi:** `PRAGMA journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`.
  - **Tranzaksiyalar:** `@asynccontextmanager async def transaction()` orqali atomik tranzaksiyalar va xatoda rollback kafolatlanadi.
  - **Migratsiyalar mexanizmi:** `schema_migrations` jadvali asosida `db/migrations/` dagi barcha `.sql` fayllarni tartib bilan avtomatik qo'llaydi (`run_migrations`).

#### SQL Migratsiyalar (`db/migrations/`):
- 📄 `0001_init_users.sql` — `users` jadvalini yaratadi. Telegram foydalanuvchilarini ro'yxatdan o'tkazish, rollari (`student`, `mentor`, `admin`) va faollik holatini (`active`, `blocked`) saqlaydi.
- 📄 `0002_license_nodes.sql` — `license_nodes` jadvalini yaratadi. Ko'p pog'onali mentorlik litsenziya tarmoqlari (daraxt), bosqichlari (`limit`, `hamkorlik`, `independent`), KPI va royalti foizlarini boshqaradi.
- 📄 `0003_courses_lessons.sql` — `courses` va `lessons` jadvallarini yaratadi. Kurslar va ularga tegishli darslar tartibi, manba Telegram posti, davomiyligi hamda bepul preview holatini saqlaydi.
- 📄 `0004_access_grants.sql` — `access_grants` jadvalini yaratadi. Foydalanuvchilarning kurslar yoki alohida darslarga sotib olingan/berilgan ruxsatlarini (dostup) va amal qilish muddatlarini saqlaydi.
- 📄 `0005_delivery_tokens.sql` — `delivery_tokens` jadvalini yaratadi. Dars videolarini xavfsiz va vaqtinchalik xesh-token orqali streaming qilish, ruxsatsiz tarqalishining oldini oladi.
- 📄 `0006_sales_royalty.sql` — `sales`, `royalty_ledger`, `click_transactions`, `payme_transactions` jadvallarini yaratadi. To'lovlar, savdolar, Click/Payme tranzaksiyalari hamda mentorlar va platforma o'rtasidagi royalti hisob-kitoblarini yuritadi.
- 📄 `0007_cabinets_chat.sql` — `cabinets`, `cabinet_members`, `chat_rooms`, `chat_room_members`, `chat_messages` jadvallarini yaratadi. Mentorlarning shaxsiy kabinetlari, a'zo talabalar va kurs bo'yicha guruh chatlarini tashkil qiladi.
- 📄 `0008_mentor_userbot_ai.sql` — `mentor_userbots`, `lesson_assessment_criteria`, `comprehension_checks` jadvallarini yaratadi. Mentorlarning Telegram userbot sessiyalari, darslarni o'zlashtirish mezonlari hamda AI orqali talabaning tushunish darajasini baholash natijalarini saqlaydi.
- 📄 `0009_adaptive_unlock.sql` — `unlock_tier_rules`, `daily_unlock_plan` jadvallarini yaratadi. AI baholash baliga qarab talabaga moslashuvchan kunlik dars ochilish limitlarini (adaptive tier) belgilaydi va nazorat qiladi.
- 📄 `0010_live_sessions.sql` — `live_sessions`, `live_attendance` jadvallarini yaratadi. Jonli efirlarni (vebinarlar) rejalashtirish, o'tkazish va talabalarning qatnashish davomatini ro'yxatga oladi.
- 📄 `0011_lesson_views.sql` — `lesson_views` jadvalini yaratadi. Talabalarning har bir darsni ko'rish davomiyligi, foizi (`completion_percent`) va tugatilgan vaqtini yozib boradi.
- 📄 `0012_engagement_nudge.sql` — `engagement_activity`, `nudge_campaigns`, `nudge_messages_log` jadvallarini yaratadi. Foydalanuvchilarning faollik vaqtini kuzatish va dars qoldirgan nofaol talabalarga avtomatik eslatmalar (nudge) yuboradi.
- 📄 `0013_completion_notifications.sql` — `completion_notifications` jadvalini yaratadi. Darsni muvaffaqiyatli tugatganda talabaga yuborilgan tabrik xabarnomalarini qayd etadi va takrorlanishining oldini oladi.
- 📄 `0014_mentor_cards_auto_debit.sql` — `mentor_cards`, `royalty_auto_settlements` jadvallarini yaratadi. Quyi mentorlarning bog'langan bank kartalari va qarz royalti summalarini avtomatik yechib olish (auto-debit) operatsiyalarini saqlaydi.
- 📄 `0015_tariff_quotas.sql` — `tariff_quotas` jadvalini yaratadi. Franshiza olgan mentorlarning tariflari (`standart`, `pro`, `vip`) bo'yicha bepul beriladigan kurs dostup limitlari va qoldiqlarini boshqaradi.
- 📄 `0016_ai_agent_token_billing.sql` — `ai_token_usage` jadvalini yaratadi. Mentorlarning AI ustoz xizmatidan foydalangan tokenlari (`prompt`, `completion`) va sarflangan xarajatlarini hisoblab boradi.
- 📄 `0017_server_expense_billing.sql` — `server_expense_usage` jadvalini yaratadi. Video oqim (`bandwidth`), faol talabalar va hosting uchun sarflangan server xarajatlarini mentorlar kesimida hisobga oladi.
- 📄 `0018_live_sessions_enhanced.sql` — `live_sessions` jadvaliga yangi ustunlar (`title`, `description`, `stream_key`, `viewer_count`, `total_viewers`, `started_at`, `ended_at`) qo'shadi hamda `live_polls`, `live_poll_votes`, `live_questions`, `live_chat_messages` jadvallarini yaratadi. Jonli efirda interaktiv so'rovnomalar, savol-javoblar va chatni ta'minlaydi.
- 📄 `0019_course_tariffs.sql` — `course_tariffs` jadvalini yaratadi, `lessons`, `access_grants`, `sales` jadvallariga `required_tier` / `tier` ustunlarini qo'shadi. Kurslar uchun ko'p bosqichli tariflar (Start, Pro, VIP) va unga bog'liq dars huquqlarini belgilaydi.
- 📄 `0020_mentor_application_payment.sql` — `mentor_applications` jadvalini yaratadi. Mentorlikka topshirilgan arizalar, tajriba ma'lumotlari, to'lov summasi va to'lov kvitansiyasi (cheki) rasmini saqlaydi.
- 📄 `0021_lesson_quizzes.sql` — `lesson_quizzes`, `lesson_quiz_submissions`, `lesson_completions` jadvallarini yaratadi. Dars testlari, talabalarning test topshirish urinishlari va keyingi darsni ochish huquqini beruvchi darsni yakunlash holatini yuritadi.
- 📄 `0022_user_notifications.sql` — `user_notifications` jadvalini yaratadi. Foydalanuvchilar uchun tizimli bildirishnomalar, ularning o'qilganlik holati va havolalarini saqlaydi.
- 📄 `0023_ai_course_waitlist.sql` — `course_waitlist` jadvalini yaratadi va AI kursini kiritadi. Hali ochilmagan kurslarga qiziqish bildirgan foydalanuvchilarning kutish ro'yxatini (navbatini) shakllantiradi.
- 📄 `0024_student_feedbacks.sql` — `student_feedbacks` jadvalini yaratadi. Talabalarning darslar va kurslar bo'yicha baholari, fikr-mulohazalari (feedback) va shikoyatlarini to'playdi.
- 📄 `0025_course_notifications.sql` — `course_notifications` jadvalini yaratadi. Kurs boshlanganda va to'liq yakunlanganda talabaga yuboriladigan tabrik xabarlarini atomik bron qilish va parallel poygalardan (race condition) himoyalaydi.
- 📄 `0026_broadcasts_and_course_waitlist.sql` — `broadcasts` jadvalini yaratadi va `courses` jadvaliga `is_waitlist` ustunini qo'shadi. Adminlar tomonidan ommaviy xabarnomalar monitoringi va kurslarni interaktiv navbat (waitlist) rejimiga o'tkazishni ta'minlaydi.

---

### 🌟 So'nggi Tasdiqlangan Tuzatishlar va Yangilanishlar:
- ⚡️ `Bot Username Kesh va Tarmoq Himoyasi`: `profile.py` va `mentor/cabinet.py` fayllarida `_resolve_bot_username` joriy etildi. Har safar Telegramga ortiqcha so'rov yuborilmaydi, xotiradan 0ms da olinadi va tarmoq uzilishlarida (`WinError 64`) xatolik bermasdan zaxira nomdan foydalanadi.
- 📩 `Sotuv Havolalarini 2 Qismga Bo'lish`: `profile.py` va `mentor/cabinet.py` da sotuv havolalari xabari qulay o'qilishi uchun 2 ta xabarga ajratildi (1-xabar: Online sotuv Click/Payme havolalari, 2-xabar: Lichkada to'laganlar uchun ochiq havolalar va umumiy kabinet taklif havolasi).
- 👤 `UserService va Kontakt Qabuli`: `services/user_service.py` konstruktori xavfsiz holatga keltirildi va `update_profile` metodi qo'shildi; `start.py` dagi `handle_contact` da telefon raqam yuborilganda `TypeError` va `AttributeError` xatolari to'liq bartaraf etildi.
- 💳 `Click va Payme Statik Logolari`: `web/main.py` da `/images` papkasi `StaticFiles` orqali ulandi (SPA fallback o'rniga to'g'ri PNG rasm qaytaradi), `PaymentModal.tsx` da rasm yuklanmay qolishiga qarshi avtomatik fallback qo'shildi va frontend production build qilindi.

---

### 4. 🗄️ Repozitoriylar Qatlami (`BilimGo/db/repositories/`)

- 📄 `access_grant_repo.py` (`AccessGrantRepository`) — Kurslar va darslarga foydalanuvchi dostup huquqlarini yaratish, tekshirish va talabaning kurslardagi progressini olish. Metodlari: `grant_course_access`, `has_active_access`, `count_active_courses`, `get_latest_active_course_title`, `count_cohort_students`, `get_user_course_enrollment_time`, `get_student_courses_with_progress`.
- 📄 `admin_repo.py` (`AdminRepository`) — Super admin va platforma uchun umumiy statistika, mentorlar, darslar, savdolar, auditoriya tahlili va kabinet talabalarining faollik hisobotlarini olish. Metodlari: `get_overall_stats`, `get_platform_overview`, `get_cabinet_students_activity_rows`, `get_courses_and_counts`, `get_mentors_list`, `get_all_submentors_overview`, `get_mentor_courses_and_counts`, `get_quota_mentors_list`.
- 📄 `ai_token_repo.py` (`AITokenRepository`) — Mentorlar va talabalar o'rtasidagi AI o'qituvchi token sarflarini qayd etish va xarajatlar tahlilini hisoblash. Metodlari: `record_usage`, `get_mentor_summary`, `list_mentor_recent_usage`.
- 📄 `assessment_criteria_repo.py` (`AssessmentCriteriaRepository`) — Darslarning AI baholash mezonlari (kalit tushunchalar va minimal o'tish bali)ni saqlash va olish. Metodlari: `get_by_lesson`, `upsert`.
- 📄 `base.py` (`BaseRepository`) — Barcha repozitoriylar uchun asosiy tayanch klass; umumiy DB ulanish kontekstini ta'minlaydi.
- 📄 `broadcast_repo.py` (`BroadcastRepository`) — Admin va mentorlar tomonidan ommaviy xabarnomalar yuborish tarixi, holati hamda maqsadli auditoriya Telegram ID larini saralab olish. Metodlari: `create_broadcast`, `update_broadcast_status`, `get_active_user_telegram_ids`, `get_active_mentor_telegram_ids`, `get_user_telegram_id_by_id`, `get_mentor_course_audience_telegram_ids`, `get_mentor_all_audience_telegram_ids`, `get_course_students_telegram_ids`, `get_course_all_users_telegram_ids`.
- 📄 `cabinet_repo.py` (`CabinetRepository`) — Mentorlik kabinetlarini yaratish, talabalarni kabinetga a'zo qilish, brending sozlamalarini boshqarish va kabinet ma'lumotlarini olish. Metodlari: `get_by_owner_node`, `create`, `add_member`, `is_member`, `list_students`, `count_students`, `list_my_cabinets`, `get_owned_cabinet_ids`, `get_user_cabinets_with_details`, `create_cabinet_record`, `get_branding_config`, `update_cabinet_branding`, `delete_cascade`, `get_student_mentor_owner_id`.
- 📄 `chat_repo.py` (`ChatRepository`) — Kabinet va kurslar bo'yicha guruh chat xonalarini ochish, xabarlar yozish, o'qilganlik holatini yangilash va xabarlar tarixini olish. Metodlari: `get_room`, `create_room`, `add_room_member`, `is_room_member`, `send_message`, `list_messages_after`, `update_last_read`, `list_rooms_for_cabinet`, `get_room_by_id`, `get_first_room_for_cabinet`, `resolve_or_create_room`, `list_messages_with_users`.
- 📄 `click_transaction_repo.py` (`ClickTransactionRepository`) — Click to'lov tizimi tranzaksiyalarini tayyorlash (`prepared`) va tasdiqlash (`confirmed`) holatlarini boshqarish. Metodlari: `create_if_absent`, `mark_confirmed`.
- 📄 `completion_notification_repo.py` (`CompletionNotificationRepository`) — Darslar va kurslarni tamomlash xabarnomalarining yuborilganlik holatini kuzatish hamda kurs xabarnomalarini atomik bron qilish. Metodlari: `is_notified`, `mark_notified`, `try_claim_course_notification`, `mark_course_notified`, `is_course_notified`.
- 📄 `comprehension_check_repo.py` (`ComprehensionCheckRepository`) — O'quvchining darsni tushunganligini tekshirish javoblarini yozish, kutilayotgan javoblarni ro'yxatlash va AI baholash natijalarini kiritish. Metodlari: `create_pending`, `list_pending`, `mark_evaluated`, `mark_failed`, `get_latest_score`.
- 📄 `course_repo.py` (`CourseRepository`) — Kurslar katalogi, e'lon matnlari, muqova rasmlari va kursning waitlist holatini yangilash. Metodlari: `get_by_id`, `list_published`, `update_waitlist_status`, `update_notice_text`, `update_image_url`.
- 📄 `course_tariff_repo.py` (`CourseTariffRepository`) — Kurslarning ko'p bosqichli tarif rejalari (Start, Pro, VIP) ma'lumotlari va xususiyatlarini (JSON features) olish. Metodlari: `get_by_course_id`, `get_by_id`.
- 📄 `daily_unlock_plan_repo.py` (`DailyUnlockPlanRepository`) — Moslashuvchan dars ochilishi (adaptive unlock) bo'yicha talabaning bugungi ruxsat etilgan darslar limitini saqlash va yangilash. Metodlari: `get_latest`, `upsert_today`.
- 📄 `delivery_token_repo.py` (`DeliveryTokenRepository`) — Xavfsiz video dars ko'rish uchun vaqtinchalik xesh-tokenlarni yaratish, tekshirish va aktivatsiya qilish. Metodlari: `create`, `get_by_hash`, `mark_activated`.
- 📄 `engagement_repo.py` (`EngagementRepository`, `NudgeRepository`) — Talabalarning so'nggi faolligini qayd etish, uzoq vaqt kirmaganlarni aniqlash hamda jalb qiluvchi kampaniyalarni (nudge) bosqichma-bosqich yurgizish. Metodlari: `touch`, `list_inactive_since`, `get_active_campaign`, `start_campaign`, `advance_step`, `exhaust_campaign`, `stop_campaign`.
- 📄 `lesson_repo.py` (`LessonRepository`) — Darslar ro'yxati, tartibi va Telegram manba postidan dars matnini xavfsiz o'qib olish. Metodlari: `get_by_id`, `list_by_course`, `get_source_post_text`.
- 📄 `lesson_view_repo.py` (`LessonViewRepository`) — Dars ko'rish seanslarini boshlash, ko'rilgan vaqt va foizni yangilash, kurs progressi va talabaning kunlik o'qish statistikasini (streak, heat-map) hisoblash. Metodlari: `start_view`, `get_latest_view_id`, `update_progress`, `student_progress_for_course`, `mentor_students_activity`, `get_user_study_stats`, `get_streak_days`, `get_daily_activity_map`.
- 📄 `license_node_repo.py` (`LicenseNodeRepository`) — Franshiza va mentorlik litsenziya tarmoqlari (daraxti), zanjirli ota-tugunlarni (CTE) aniqlash, bosqich va statuslarni boshqarish hamda 15 kunlik limit muddatini tekshirish. Metodlari: `get_by_id`, `get_ancestors`, `update_stage`, `update_status`, `get_by_owner_id`, `is_limit_expired`, `create_node`, `update_course_id`.
- 📄 `live_session_repo.py` (`LiveSessionRepository`) — Vebinar va jonli efirlarni yaratish, holatini o'zgartirish (`scheduled`, `live`, `ended`), qatnashuvchilarni qayd qilish va maqsadli talabalar auditoriyasini olish. Metodlari: `create`, `get_by_id`, `list_upcoming`, `set_status`, `record_join`, `record_leave`, `expire_old_scheduled_sessions`, `list_upcoming_with_details`, `get_user_role`, `get_course_active_students_audience`, `get_mentor_course_audience_students`.
- 📄 `mentor_application_repo.py` (`MentorApplicationRepository`) — Yangi mentorlik arizalarini qabul qilish, arizalar holatini boshqarish va to'lov kvitansiyasini (cheki) saqlash. Metodlari: `create`, `get_latest_by_user_id`, `get_by_id`, `list_all`, `update_status`, `submit_receipt`.
- 📄 `mentor_card_repo.py` (`MentorCardRepository`) — Quyi mentorlarning Click/Payme bank kartalarini bog'lash, saqlash, faol kartani topish va kartani o'chirish (deaktivatsiya). Metodlari: `save_card`, `get_active_card`, `deactivate_card`.
- 📄 `mentor_userbot_repo.py` (`MentorUserbotRepository`) — Mentorlarning Telegram userbot sessiyalari ulanish holatini boshqarish va saqlash. Metodlari: `get_by_mentor`, `upsert_connected`, `mark_disconnected`.
- 📄 `payme_transaction_repo.py` (`PaymeTransactionRepository`) — Payme to'lov tizimi tranzaksiyalarini yaratish, amalga oshirish (`state=2`) va bekor qilish holatlarini saqlash. Metodlari: `get_by_id`, `create`, `mark_performed`, `mark_cancelled`.
- 📄 `quiz_repo.py` (`QuizRepository`) — Dars testlari (savol va variantlar)ni saqlash, talabaning javob urinishlarini qayd qilish va darsni yakunlangan (`completed`) deb belgilash. Metodlari: `get_by_lesson_id`, `get_by_id`, `create_quiz`, `record_attempt`, `get_user_attempts_for_lesson`, `mark_lesson_completed`.
- 📄 `royalty_repo.py` (`RoyaltyLedgerRepository`) — Sotuvlardan tushgan mablag'lar bo'yicha mentorlar va platforma royalti yozuvlarini yuritish, yechilmagan qarz hisoblarini olish va avtomatik yechib olishlarni qayd etish. Metodlari: `create_entry`, `exists_for_sale`, `unsettled_total_for_node`, `settle_for_node`, `unsettled_info_for_child_node`, `settle_for_child_node`, `record_auto_settlement`.
- 📄 `sale_repo.py` (`SaleRepository`) — Kurs sotuvlarini yaratish (`pending`), to'langan deb belgilash (`paid`), bekor qilish yoki to'lovni qaytarish (`refunded`). Metodlari: `create_pending`, `get_by_id`, `mark_paid`, `mark_failed`, `mark_refunded`.
- 📄 `server_expense_repo.py` (`ServerExpenseRepository`) — Mentorlar uchun server xarajatlarini (video oqim, faol talabalar, xosting) hisoblab borish va umumiy sarf-xarajatlar hisobotini taqdim etish. Metodlari: `record_expense`, `get_mentor_summary`, `list_mentor_recent`, `resolve_student_mentor_id`.
- 📄 `tariff_quota_repo.py` (`TariffQuotaRepository`) — Yangi mentorlar uchun tarifiga muvofiq kurs limitlarini avtomatik ochish, limit sarflanishini nazorat qilish va admin tomonidan qo'shimcha limit berish. Metodlari: `initialize_quotas_for_tariff`, `list_by_node`, `get_quota_for_course`, `consume_quota`, `add_quota_amount`, `set_quota_amount`.
- 📄 `unlock_tier_repo.py` (`UnlockTierRuleRepository`) — AI tekshiruv bali oraliqlari (`min_score`, `max_score`) asosida mos keladigan kunlik dars limit qoidasini (kursga xos yoki global standart) topish. Metodlari: `find_tier`.
- 📄 `user_repo.py` (`UserRepository`) — Foydalanuvchilarni Telegram ID orqali yaratish yoki olish, rolini, telefon raqamini, profilini yangilash va unga biriktirilgan mentor/kabinet ma'lumotlarini aniqlash. Metodlari: `get_by_id`, `get_by_telegram_id`, `get_or_create`, `update_role`, `update_phone`, `update_profile`, `set_status`, `list_mentors_with_nodes`, `get_user_assigned_mentor_and_cabinet`.

---

### 5. 🧠 Biznes Mantiq Servislari Qatlami (`BilimGo/services/`)

- 📄 `access_control_service.py` — Darslarga kirish huquqini ko'p bosqichli tekshirish servisi. Darsning bepul (`is_free_preview`), foydalanuvchining imtiyozli roli (`admin`, `super_mentor`, `mentor` to'siqsiz ko'ra oladi), sotib olingan kurs huquqi (`has_active_access`) va `AdaptiveUnlockService` dagi kunlik dars ochilish limitini tekshiradi. Metodlari: `ensure_can_watch`, `create_default`.
- 📄 `adaptive_unlock_service.py` — Talabaning tushunish balli (comprehension check) ga asosan darslarni kunma-kun bosqichma-bosqich ochib boruvchi moslashuvchan limit servisi (kumulyativ dars cheklovi). Metodlari: `get_effective_limit`, `_advance_plan`.
- 📄 `admin_notifier.py` — Telegram Forum Supergroup mavzulariga (Topics: mentorlik arizalari, to'lov cheklari va avtomat to'lovlar, statistika, foydalanuvchilar va tizim ogohlantirishlari) yoki adminlar shaxsiy chatiga xabarnomalar yuboruvchi markaziy servis (HTTPX va Aiogram qo'llab-quvvatlaydi). Metodlari: `send_to_topic`, `send_mentor_application`, `send_payment_receipt`, `send_payment_alert`, `send_statistics_alert`, `send_user_alert`, `send_waitlist_alert`, `send_feedback_alert`, `send_system_alert`, `send_alert`.
- 📄 `ai_evaluation_service.py` — Talabaning dars yuzasidan yozgan javobini belgilangan mezon bilan solishtirib, 0 dan 100 gacha baholovchi AI servisi (Gemini 2.0 Flash -> Claude -> lokal qoidalar kaskadi). Bahoni bazaga saqlaydi, userbot orqali o'quvchiga yetkazadi va darsni yakunlash logikasini chaqiradi. Metodlari: `evaluate_pending_batch`, `_evaluate_one`.
- 📄 `ai_tutor_service.py` — Kurs yo'nalishi bo'yicha ixtisoslashgan (Logistika, Telegram Ads, Konkurs, Sayt, Xitoy importi) interaktiv AGY AI Ustoz servisi. Gemini va Claude yordamida o'zbek tilida savollarga tushunarli javob beradi va sarflangan tokenlar haqini mentor hisobiga yozib boradi. Metodlari: `ask_tutor`, `resolve_student_mentor_id`, `_generate_contextual_response`.
- 📄 `analytics_service.py` — Dars ko'rish progressi va o'zlashtirish ko'rsatkichlarini hisoblash servisi. Video boshlanishi va foizini yozadi, talaba natijalarini chiqaradi hamda Super Admin va mentorlar uchun umumiy platforma va kabinetlar faollik hisobotlarini shakllantiradi. Metodlari: `record_view_start`, `record_progress`, `get_student_progress`, `get_cabinet_activity`, `get_platform_overview`, `get_cabinet_students_activity`.
- 📄 `auto_debit_service.py` — Mentordan royalti komissiyasini ulangan plastik kartadan (Payme va Click Subscribe API) har 10-15 ta o'quvchi xarididan keyin avtomatik yechib olish servisi. Karta ulanmagan yoki mablag' yetmagan taqdirda mentor litsenziyasini to'xtatadi (`suspended`) va ogohlantiradi. Metodlari: `charge_card`, `_charge_payme`, `_charge_click`, `check_and_auto_debit_royalty`.
- 📄 `broadcast_service.py` — Butun platforma yoki maqsadli guruhlarga (mentorlar, kurs talabalari, shogirdlar, navbatdagilar) Telegram bot orqali ommaviy matn, rasm yoki nusxalangan xabarlarni tarqatish servisi. Telegram `FloodWait / RetryAfter` cheklovidan himoyalangan. Metodlari: `resolve_audience`, `execute_broadcast`, `copy_broadcast`.
- 📄 `cabinet_service.py` — Litsenziyali mentorlar uchun o'quv kabinetlari va guruh chatlarini boshqarish servisi. Xariddan so'ng talabani avtomatik biriktiradi, kabinet brendingi va sozlamalarini yangilaydi hamda kaskad o'chirishni ta'minlaydi. Metodlari: `get_or_create_for_node`, `enroll_student_after_purchase`, `get_or_create_mentor_node_and_cabinet`, `get_mentor_students`, `list_user_cabinets`, `get_user_cabinets`, `create_cabinet_flow`, `update_cabinet_branding`, `delete_cabinet`.
- 📄 `click_service.py` — Click to'lov tizimining server protokoli integratsiyasi (Prepare va Complete bosqichlari). MD5 xesh imzoni tekshiradi, tranzaksiya summasini nazorat qiladi va muvaffaqiyatli to'lovda `PaymentService` orqali kursga kirishni ochadi. Metodlari: `_verify_prepare_sign`, `_verify_complete_sign`, `prepare`, `complete`.
- 📄 `cohort_service.py` — Kurslardagi oqim (potok/cohort) raqamini avtomatik hisoblovchi yordamchi servis (har oy 1.x, 2.x; har 20 ta o'quvchi uchun .0, .1, .2) va kurs sarlavhalarini patok bilan boyitish vazifasini bajaradi. Metodlari: `calculate_course_cohort`, `format_course_title_with_cohort`.
- 📄 `course_service.py` — Kurslar, ularning patoklari, tariflari va o'quv dasturlarini boshqarish servisi. Talabaning dars o'zlashtirish progressini hisoblaydi, kutish ro'yxati (waitlist) arizalarini boshqaradi va admin tomonidan kurs sozlamalarini (e'lon, rasm, waitlist holati) yangilaydi. Metodlari: `list_published`, `get_by_id`, `get_course_cohort`, `get_formatted_title`, `get_course_with_tariffs`, `get_student_courses_progress`, `get_waitlist_status`, `join_waitlist`, `leave_waitlist`, `toggle_waitlist`, `set_course_notice`, `set_course_image`.
- 📄 `delivery_token_service.py` — Video va o'quv materiallarini xavfsiz uzatish uchun cheklangan vaqtli (TTL) bir martalik SHA-256 xeshli tokenlarni generatsiya qilish va manbani brauzerdan yashirgan holda tekshirib darsni qaytarish servisi. Metodlari: `issue`, `resolve`.
- 📄 `engagement_monitor_service.py` — O'quvchilarning faolligini nazorat qilish va 24 soatdan ortiq dars ko'rmagan passiv talabalarni aniqlab, ularga 4 bosqichli eskalatsiya eslatmalarini rejalashtirish servisi. Metodlari: `touch_activity`, `scan_and_advance`.
- 📄 `lesson_completion_service.py` — Dars ko'rish progressi va xabarnomalar servisi. Talaba kursning 1-darsini boshlaganda 1 ta tabrik, eng oxirgi darsini tugatganda 1 ta yakuniy tabrik xabari yuboradi (oraliq darslarda bezovta qilmaydi; atomik lock bilan parallel so'rovlardan himoyalangan). Metodlari: `handle_lesson_progress`, `handle_lesson_completed`, `_check_and_notify_course_started`, `_check_and_notify_course_completed`.
- 📄 `live_session_service.py` — Jonli efirlarni rejalashtirish, ro'yxatini shakllantirish, muddati o'tgan (3 soatdan oshgan) efirlarni avtomatik yakunlash, kirish huquqini tekshirish va mentor auditoriyasiga xoslab xabarnoma yuborish servisi. Metodlari: `schedule`, `list_upcoming`, `get_session`, `start`, `end`, `join`, `leave`, `get_session_audience_students`.
- 📄 `live_stream_service.py` — Real vaqt rejimida WebRTC Video/Audio striming va WebSocket signalizatsiya menejeri (`LiveStreamManager`). Jonli chat, emojilar, qo'l ko'tarish, mikrofon boshqaruvi, so'rovnomalar (poll) va tomoshabinlar oqimini boshqaradi.
- 📄 `messaging_service.py` — Kabinet ichki guruh chat xabarlarini boshqarish servisi. Xona a'zoligini nazorat qiladi, yangi xabarlarni saqlaydi va o'qilganlik (`last_read`) ko'rsatkichini yangilaydi. Metodlari: `send_message`, `poll_new_messages`, `resolve_room`, `get_room_messages`, `send_room_message`.
- 📄 `payme_service.py` — Payme Merchant JSON-RPC API integratsiyasi. Tranzaksiyalarni tekshirish, yaratish, amalga oshirish va bekor qilish bosqichlarini boshqaradi hamda to'lov yakunlangach kursga kirishni tasdiqlaydi. Metodlari: `dispatch`, `_check_perform`, `_create`, `_perform`, `_cancel`, `_check`.
- 📄 `payment_service.py` — Xaridlar va to'lovlarning markaziy biznes servisi. Buyurtma yaratish (`initiate_purchase`), to'lovni tasdiqlash (`confirm_payment`), kursga kirish ruxsatini ochish, royalti taqsimotini amalga oshirish, talabani kabinetga qo'shish va avto-debitni ishga tushirishni bajaradi. Metodlari: `initiate_purchase`, `confirm_payment`.
- 📄 `quiz_service.py` — Darslar bo'yicha test savollarini taqdim etish va javoblarni tekshirish servisi. Talabaning urinishlarini yozadi, to'g'ri/noto'g'ri ekanligini baholaydi va barcha testlar topshirilganda darsni muvaffaqiyatli yakunlaydi. Metodlari: `get_lesson_quizzes`, `check_answer`, `get_lesson_status`.
- 📄 `royalty_service.py` — Ko'p bosqichli litsenziya daraxti bo'ylab daromad (royalti) taqsimoti servisi. 15 kunlik Limit davrida 0% royalti (100% o'quvchida qoladi, kvotadan yechiladi) va keyingi bosqichlarda ota tugunlar bo'ylab belgilangan foizda ulushlarni kaskadli hisoblaydi. Metodlari: `distribute_for_sale`.
- 📄 `user_service.py` — Foydalanuvchilar profili, rollari, mentorlik arizalari, o'quv statistikasi va faollik grafiklarini boshqaruvchi markaziy servis. Metodlari: `get_by_id`, `get_by_telegram_id`, `get_or_create`, `get_user_profile`, `update_user_status`, `update_role`, `get_full_profile`.

---

### 6. ⚙️ Core va Konfiguratsiya Qatlami (`BilimGo/core/`)

- 📄 `core/cache.py` — Asinxron In-Memory keshlash servisi (`CacheService`); ma'lumotlarni TTL (yashash muddati) bilan xotirada saqlash, olish, o'chirish va tozalash (`get`, `set`, `delete`, `clear`) vazifalarini bajaradi.
- 📄 `core/config.py` — Loyihaning markaziy konfiguratsiyasi va `.env` o'zgaruvchilarini yuklash moduli (`Settings`); Bot, Database, Relay (Userbot), Delivery tokenlari, Click, Payme, Anthropic (Claude), Gemini AI, WebApp URL va fayl yo'llari konfiguratsiyalarini boshqaradi.
- 📄 `core/exceptions.py` — Loyihaning domen darajasidagi maxsus istisnolar iyerarxiyasi (`BilimGoError`, `AccessDeniedError`, `NotFoundError`, `MigrationError`); xatoliklarni tizimli va xavfsiz boshqarishga xizmat qiladi.

---

### 7. 🌐 FastAPI Web API va Routerlar (`BilimGo/web/`)

- 📄 `web/main.py` — FastAPI asosiy dastur kirish nuqtasi (`FastAPI`, CORS sozlamalari, barcha 15 ta routerni ulash, lifespan kontekst menejeri orqali ma'lumotlar bazasi va migratsiyalarni ishga tushirish hamda React Mini App SPA statik fayllarini kesh nazorati bilan yetkazish).
- 📄 `web/dependencies/auth.py` — FastAPI autentifikatsiya bog'liqligi (`get_current_telegram_id`); Telegram WebApp `initData` ma'lumotlarini HMAC-SHA256 orqali tekshirish, foydalanuvchi Telegram ID sini xavfsiz aniqlash va soxta so'rovlarni 401 xatolik bilan to'xtatish vazifasini bajaradi.

#### API Routerlari (`web/routers/`):
- 📄 `web/routers/admin_analytics.py` — Admin va mentorlar uchun tahliliy ko'rsatkichlar routeri; platforma umumiy tahlili (`GET /api/analytics/overview`, `GET /api/analytics/admin/overview`), talabaning dars o'zlashtirish progressi (`GET /api/analytics/courses/{course_id}/my-progress`) va kabinet o'quvchilari faolligi statistikasi (`GET /api/analytics/cabinets/activity`).
- 📄 `web/routers/ai_tutor.py` — Darslar bo'yicha shaxsiy AI Tyutor va token sarfi routeri; video darslar ostida sun'iy intellektga savol berish (`POST /api/ai/lesson-chat`, `POST /api/ai/ask-lesson`) hamda mentorlar uchun shogirdlarning AI token sarfi hisobotini olish (`GET /api/ai/mentor-token-stats`).
- 📄 `web/routers/cabinet.py` — Mentorlar va adminlar kabinetlarini boshqarish routeri; o'z kabinetlarini olish (`GET /api/cabinets/me`), kabinet o'quvchilari (`GET /api/cabinets/{cabinet_id}/students`), chat xonalari (`GET /api/cabinets/{cabinet_id}/rooms`), yangi kabinet ochish (`POST /api/cabinets`), kabinet brendingini yangilash (`PUT /api/cabinets/{cabinet_id}`) va o'chirish (`DELETE /api/cabinets/{cabinet_id}`).
- 📄 `web/routers/cards.py` — Mentorlarning bank kartalarini ulash va avto-to'lovlar routeri; faol kartani tekshirish (`GET /api/cards/my-card`), Payme/Click karta tokenizatsiyasi va SMS kod so'rash (`POST /api/cards/bind/initiate`), SMS kodni tasdiqlash (`POST /api/cards/bind/verify`) hamda kartani uzish (`POST /api/cards/unbind`).
- 📄 `web/routers/chat.py` — Talabalar va mentorlar o'rtasidagi ichki chat tizimi routeri; kabinet guruhiga xabar yuborish (`POST /api/chat/rooms/{room_id}/messages`) va yangi xabarlarni doimiy o'qib olish (`GET /api/chat/rooms/{room_id}/messages`).
- 📄 `web/routers/feedback.py` — Foydalanuvchilar fikr-mulohazalari routeri; dars yoki platforma bo'yicha baho va taklif yuborish (`POST /api/feedback`), adminga Telegram orqali xabar berish, adminlar uchun barcha mulohazalarni olish (`GET /api/feedback/admin/all`) va o'z sharhlarini ko'rish (`GET /api/feedback/my`).
- 📄 `web/routers/live.py` — Jonli efirlar (Live Sessions) boshqaruvi routeri; kursga tegishli efirlarni olish (`GET /api/live/courses/{course_id}/sessions`), efir tafsiloti (`GET /api/live/sessions/{session_id}`), efirga ulanish/ruxsatni tekshirish (`POST /api/live/sessions/{session_id}/join`), efirdan chiqish (`POST /api/live/sessions/{session_id}/leave`), efirni boshlash (`POST /api/live/sessions/{session_id}/start`) va yakunlash (`POST /api/live/sessions/{session_id}/end`).
- 📄 `web/routers/live_websocket.py` — Jonli efirlar uchun real-vaqt WebSocket routeri (`/live/ws/{session_id}`); WebApp initData orqali xavfsiz ulanish, WebRTC signaling, xabarlar va qatnashuvchilar holatini real-vaqt rejimida boshqaradi.
- 📄 `web/routers/notifications.py` — Tizim va o'quv xabarnomalari routeri; foydalanuvchi bildirishnomalarini ko'rish (`GET /api/notifications`), bitta xabarni o'qilgan deb belgilash (`POST /api/notifications/{notification_id}/read`) va barcha xabarlarni o'qilgan qilish (`POST /api/notifications/read-all`).
- 📄 `web/routers/payments.py` — To'lovlar va hisob-kitob integratsiyasi routeri; kurs sotib olishni boshlash (`POST /api/payments/purchase/initiate`), Click webhook tayyorlash va yakunlash (`POST /api/payments/click/prepare`, `POST /api/payments/click/complete`), Payme JSON-RPC webhooklarini qayta ishlash (`POST /api/payments/payme`).
- 📄 `web/routers/player.py` — Darslar, media pleyer va streaming routeri; kurslar ro'yxati (`GET /api/courses`), kurs tafsilotlari (`GET /api/courses/{course_id}`), kursni sozlash (`PATCH /api/courses/{course_id}/customize`), darslar ro'yxati va kirish huquqlari (`GET /api/courses/{course_id}/lessons`), xavfsiz delivery token yaratish (`POST /api/lessons/{lesson_id}/access-token`), dars o'zlashtirish progressini yangilash (`POST /api/lessons/{lesson_id}/progress`), ovozli hisobot topshirish va mentorga yetkazish (`POST /api/lessons/{lesson_id}/voice-report`), dars rasmlarini uzatish (`GET /api/media/{channel_id}/{filename}`) va HTTP Range orqali videoni oqimli uzatish (`GET /api/stream/{raw_token}`).
- 📄 `web/routers/quiz.py` — Darslar bo'yicha interaktiv testlar routeri; dars testlarini olish (`GET /api/quizzes/lesson/{lesson_id}`), test javobini tekshirish (`POST /api/quizzes/{quiz_id}/submit`) va dars bo'yicha test topshirish holatini olish (`GET /api/quizzes/lesson/{lesson_id}/status`).
- 📄 `web/routers/server_expenses.py` — Server va video trafigi xarajatlari routeri; mentorlar uchun o'z shogirdlarining video strimingi va hosting sarf-xarajatlari hisobotini ko'rsatish (`GET /api/server-expenses/mentor-summary`).
- 📄 `web/routers/users.py` — Foydalanuvchilar va mentorlar boshqaruvi routeri; profil ma'lumotlarini olish (`GET /api/users/profile`), profilni yangilash (`PUT /api/users/profile`), Telegram profil rasmini olish (`GET /api/users/{telegram_id}/avatar`), ochiq mentorlar katalogi (`GET /api/mentors`), mentorlik arizasini berish (`POST /api/users/mentor-application`), o'z arizasi holatini ko'rish (`GET /api/users/mentor-application/my`) va ariza to'lov chekini yuklash (`POST /api/users/mentor-application/receipt`).
- 📄 `web/routers/waitlist.py` — Kurslar kutish ro'yxati (Waitlist) routeri; kurs navbati holatini ko'rish (`GET /api/courses/{course_id}/waitlist`), navbatga yozilish (`POST /api/courses/{course_id}/waitlist`), navbatdan chiqish (`DELETE /api/courses/{course_id}/waitlist`), adminlar uchun navbatdagilar ro'yxati (`GET /api/courses/{course_id}/waitlist/users`) va navbatdagilarga e'lon tarqatish (`POST /api/courses/{course_id}/waitlist/broadcast`).

---

### 8. 📦 Fon Jarayonlari va Workerlar (`BilimGo/workers/`)

- 📄 `workers/ai_evaluation_worker.py` — Darslar yakunidagi talabalar yozma javoblarini AI orqali baholash fon vositasi; ma'lumotlar bazasidagi tekshirilmagan (`pending`) tushunish tekshiruvi (`comprehension_check`) topshiriqlarini navbat bilan olib, AI xizmati orqali mezonlar asosida avtomatik baholaydi va progressni yangilaydi.
- 📄 `workers/engagement_monitor_worker.py` — O'quvchilar faolligini doimiy nazorat qiluvchi va nofaol talabalarga rag'batlantiruvchi eslatmalar (Nudges) yuboruvchi fon xizmati; ma'lum muddat dars ko'rmagan o'quvchilarni aniqlab, ularga Telegram bot orqali avtomatik motivatsion xabarlar jo'natadi.

---

### 9. 🎨 Frontend Qatlami (`frontend/src/`)

- 📄 `frontend/src/App.tsx` — Mini App'ning asosiy boshqaruvchi (Root) komponenti. Telegram WebApp integratsiyasi, BackButton sinxronizatsiyasi, ekranlararo marshrutlash (routing), mavzular va unread xabarnomalar hisobini boshqaradi.
- 📄 `frontend/src/types.ts` — Frontend uchun barcha TypeScript interfeyslari (kurslar, tariflar, darslar, kabinetlar, chat, jonli efir, profillar, ro'yxatlar va navigatsiya ko'rinishlari).
- 📄 `frontend/src/main.tsx` — React ilovasining kirish nuqtasi, ErrorBoundary bilan himoyalangan bo'lib, kutilmagan xatolarda xotirani tozalab qayta yuklash imkonini beradi.
- 📄 `frontend/src/services/api.ts` — Backend API bilan aloqa qiluvchi to'liq HTTP klient moduli (kurslar, darslar, to'lovlar, kabinet chat, WebRTC, AI ustoz, statistika va sozlamalar).
- 📄 `frontend/src/services/telegram.ts` — Telegram Mini App SDK bilan to'liq integratsiya wrapperi (mavzularni aniqlash, BackButton, MainButton, HapticFeedback, initData, start_param).

#### Frontend Komponentlari va Ekranlari (`frontend/src/components/`):
- 📄 `AdminDashboardView.tsx` — Super admin boshqaruv paneli: umumiy daromad, foydalanuvchilar, mentorlar, kurslar soni, o'quvchilar fikr-mulohazalari va platforma dinamikasini ko'rsatadi.
- 📄 `ApiSettingsModal.tsx` — Backend API URL manzilini va ilova mavzusini (Light / Dark / Auto) moslashuvchan o'zgartirish va sinab ko'rish modali.
- 📄 `BottomTabBar.tsx` — Telegram uslubidagi suzuvchi pastki navigatsiya paneli (Katalog, Kurslarim, Kabinet, Profil) hamda yangi xabarlar hisoblagich badgelari.
- 📄 `CabinetChatView.tsx` — Mentor va o'quvchilar uchun shaxsiy yopiq guruh chat interfeysi (xabarlar almashish, reply, Telegram animatsiyali stikerlari va kabinet sozlamalari).
- 📄 `CardBindingModal.tsx` — Mentorlar uchun Click / Payme to'lov kartalarini ulash va SMS-kod (OTP) orqali tasdiqlash interaktiv modali.
- 📄 `CatalogView.tsx` — Barcha mavjud kurslar katalogi (qidiruv, toifalar bo'yicha filtr, kurs kartochkalari, narx va davomiylik ko'rsatkichlari).
- 📄 `ContentProtection.tsx` — Dars materiallarini skrinshot, ekranni yozib olish va nusxalashdan himoyalovchi xavfsizlik qatlami (adminlar uchun avtomatik to'siqsiz).
- 📄 `CourseDetailView.tsx` — Kursning to'liq sahifasi: dastur rejasi (syllabus), tariflar tanlovi, jonli efirlar, darslar ro'yxati, kutish ro'yxati (waitlist) va xarid tugmasi.
- 📄 `FeedbackModal.tsx` — Talabalar dars yoki kurs bo'yicha Like / Dislike reaksiyalari va tezkor teglar orqali fikr-mulohaza qoldiruvchi interaktiv modal.
- 📄 `LessonAiAssistant.tsx` — Dars ekrani uchun qulay suzuvchi tugma (FAB) va Bottom Sheet ko'rinishidagi AGY AI Ustoz suhbat paneli (kun va tun rejimlariga 100% mos).
- 📄 `LessonQuizCard.tsx` — Dars oxiridagi interaktiv test kartochkasi: javoblarni tekshirish, izoh ko'rsatish va to'g'ri topshirilganda avtomatik keyingisiga o'tish imkoniyati.
- 📄 `LiveSessionsView.tsx` — Kurs doirasidagi rejalashtirilgan va jonli efirlar ro'yxati, sanalari, murabbiy ma'lumoti va efirga kirish oynasi.
- 📄 `LiveStreamView.tsx` — To'liq interaktiv real vaqt jonli efir xonasi (WebRTC video/audio, jonli chat, reaksiyalar, qo'l ko'tarish, ovozli savol va so'rovnomalar).
- 📄 `MentorStatsView.tsx` — Mentorlar uchun o'quvchilar o'zlashtirishi, faollik darajasi, darslarni ko'rish foizlari va shogirdlar tahlili paneli.
- 📄 `MyCoursesView.tsx` — Talaba sotib olgan faol kurslari ro'yxati, o'zlashtirish foizlari va darslarni davom ettirish tugmalari.
- 📄 `Navbar.tsx` — Ilovaning yuqori qismidagi ixcham sarlavha paneli (orqaga qaytish tugmasi, xabarnomalar qo'ng'irog'i va sozlamalar).
- 📄 `NotificationsModal.tsx` — Foydalanuvchiga yuborilgan tizim xabarnomalari, darslar va yangiliklar markazi (o'qilgan deb belgilash imkoniyati bilan).
- 📄 `PaymentModal.tsx` — Click va Payme to'lov usullari orqali kurs yoki tanlangan tarifni xarid qilish uchun to'lov oynasi.
- 📄 `ProfileView.tsx` — Foydalanuvchi shaxsiy profili, o'rganish statistikasi, kunlik faollik grafigi, mentorlik arizasini topshirish va kartalarni boshqarish.
- 📄 `RichAiContent.tsx` — AI javoblarini chiroyli formatda (Markdown, jadvallar, kod bloklari, qalin matnlar, nusxalash) render qiluvchi xavfsiz komponent.
- 📄 `TgEmoji.tsx` — Telegram formatidagi animatsiyali stikerlar va maxsus emojilarni aniqlovchi va ko'rsatuvchi yordamchi komponent.
- 📄 `TgEmojiPicker.tsx` — Telegram Premium uslubidagi animatsiyali emojilar tanlash popover paneli.
- 📄 `VideoPlayerView.tsx` — Darslarni ko'rish pleyeri: video/audio/matnli darslar, vaqtni nazorat qilish, dars konspekti va matni, dars testi (quiz), fikr bildirish (feedback), oxirgi dars ovozli hisoboti, navigatsiya va AI Ustoz; elementlar zamonaviy LMS oqimi bo'yicha (Pleyer -> Konspekt -> Test -> Feedback -> Navigatsiya) joylashtirilgan.
- 📄 `VoiceReportModal.tsx` — O'quvchi dars bo'yicha o'zlashtirgan bilimi haqida ovozli xabar (audio report) yozib, mentorga topshirish interaktiv modali.

---

### 10. 🚀 Ildizdagi Boshqaruv Skriptlari va Konfiguratsiyalar

- 📄 `run_all.py` — BilimGo tizimining barcha asosiy servislarini boshqaruvchi master orkestrator; FastAPI web-server (8000), Cloudflare tunneli, Telegram bot, AI Baholash workeri va Talabalar eslatma workerini birgalikda ishga tushiradi, to'xtab qolgan jarayonlarni avtomatik qayta yoqadi va `restart.flag` signali orqali butun tizimni yangilaydi.
- 📄 `restart.py` — BilimGo loyihasining barcha faol servislarini qayta ishga tushirish uchun signal jo'natuvchi boshqaruv skripti; `restart.flag` fayliga vaqt tamg'asini yozish orqali `run_all.py` ga restart signali yuboradi.
- 📄 `sync_courses.py` — Kurslar va ularning dasturlarini Telegram kanallaridan bazaga sinxronizatsiya qiluvchi skript.
- 📄 `docker-compose.yml` va `docker-compose.prod.yml` — Loyihaning Docker konteynerlashtirish va ishlab chiqarish (production) sozlamalari.
- 📄 `.env` va `.env.example` — Muhit o'zgaruvchilari (API kalitlari, bot tokeni, DB yo'li, to'lov xesh kalitlari).
