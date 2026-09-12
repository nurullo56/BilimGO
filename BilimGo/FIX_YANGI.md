# BilimGo — Yangi Tahlil va Kamchiliklar Ro'yxati (FIX_YANGI)

Eski `FIX.md` da "Barchasi to'liq yopildi" deyilgan bo'lsa-da, loyihada hali anchagina texnik qarz (technical debt) va chala ishlar mavjud. Quyida barcha muammolar ustuvorlik darajasi bilan keltirilgan.

---

## 🔴 P0 — O'tkir muammolar (Zudlik bilan hal qilinishi kerak)

### 1. Frontend va Backend to'liq uzilgan (Mock data)
- [ ] **Muammo:** `frontend/src/services/api.ts` faylida 1300+ qator kod yozilgan, ammo uning deyarli yarmidan ko'pi `mockCourses`, `mockLessons`, `mockAllStudentsActivity` kabi **soxta ma'lumotlardan iborat**.
- [ ] **Yechim:** Frontenddagi barcha "Mock" (offline fallback) mantiqlarini o'chirib, `fetch` orqali to'g'ridan-to'g'ri FastAPI backend'ga ulash kerak. Hozirgi holatda frontend faqat quruq UI (dizayn qobig'i) xolos.

### 2. Git (Versiya nazorati) yo'qligi
- [ ] **Muammo:** Loyiha papkasida umuman `.git` bazasi shakllantirilmagan (`git status` xato berdi). Bu shuncha qilingan mehnat kompyuter o'chib qolsa yoki bitta noto'g'ri fayl o'zgarishi qilinganda yo'qolib ketishi mumkin degani.
- [ ] **Yechim:** Darhol `git init`, `git add .`, va `git commit` qilib github/gitlab kabi masofaviy repozitoriyaga joylash.

---

## 🟡 P1 — Xatoliklarni boshqarish va Biznes mantiq

### 3. Yutib yuborilgan xatoliklar (Swallowed Exceptions)
- [ ] **Muammo:** Loyiha bo'ylab juda ko'p joyda `except Exception: pass` bloklari qoldirilgan. Ya'ni kod ishlamay qolsa ham tizim hech qanday xatolik (log) chiqarmay jim turadi. Ertaga tizimda xato chiqsa, qayerdan ekanligini topib bo'lmaydi.
- [ ] **Tuzatilishi kerak bo'lgan joylar:**
  - `services/live_stream_service.py` (252, 734-qatorlar)
  - `web/routers/player.py` (439, 494-qatorlar)
  - `web/routers/users.py` (142-qator)
  - `web/routers/live.py` (100-qator)
  - `sync_courses.py` (46-qator)
  - `bot/handlers/admin/broadcast.py` (318-qator)
  - **Yechim:** `pass` o'rniga `logger.error("Xatolik yuz berdi: ...", exc_info=True)` yozib chiqish.

### 4. Admin Panel UI yo'qligi
- [ ] **Muammo:** Backend'da `admin_analytics.py` bor, lekin `frontend/src/App.tsx` routerlarini qarasak, umuman Admin Panel dizayni yoki sahifasi qo'shilmagan.
- [ ] **Yechim:** Super-admin yoki bosh mentorlar tizimni boshqarishi, to'lovlarni ko'rishi va mentorlarni boshqarishi uchun React'da yangi `AdminDashboard` sahifalarini yaratish.

---

## 🟢 P2 — Arxitektura, Sifat va Production

### 5. "Qo'lbola" AI (Frontenddagi xato mantiq)
- [ ] **Muammo:** Backendda haqiqiy AI Worker (`ai_evaluation_worker.py` - Claude Anthropic API) yozilgan. Lekin Frontenddagi `api.ts` ichida `generateContextualFallbackAiAnswer` degan g'alati funksiya bor va u oddiy `if (q.includes('misol')) { return "..." }` kabi soxta sun'iy intellekt bo'lib xizmat qilmoqda.
- [ ] **Yechim:** Frontend o'zidan o'zi javob tuzishini (fallback) o'chirib, doim Backenddagi AI (Claude) API orqali javob oladigan qilish.

### 6. Production Sozlamalari (Deployment)
- [ ] **Muammo:** Loyihani jonli serverga (VPS) qo'yish uchun `.env` dagi URL'lar, Nginx (Reverse proxy) fayllari va Let's Encrypt (SSL/HTTPS) skriptlari oxiriga yetmagan. Hozir faqat `start_all_services.bat` yoki test Docker qilingan.
- [ ] **Yechim:** `nginx.conf`, `docker-compose.prod.yml` kabi server infrastrukturasi fayllarini yozish.
