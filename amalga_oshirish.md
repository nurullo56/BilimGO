# 📋 Amalga Oshirish Rejasi: Super Admin Uchun Mentorlar AI Token va Server Yuki Monitoringi

## 🎯 Maqsad va Vazifa
Platformada har bir mentor va ularning shogirdlari tomonidan:
1. **AI Tyutor xizmatida** qancha token sarflanganini (savollar soni, prompt/completion tokenlar, hisoblangan summa);
2. **Server va infratuzilmada** qancha yuk yeyilganini (ko'rilgan video darslar / streamlar soni, hosting/trafik, sarflangan summa);
3. **Jami infratuzilma xarajatlarini**;

Super Admin Telegram botdagi **alohida Reply tugma** (`⚡️ Server yuki va AI tokenlar`) orqali bir marta bosishda to'liq va tushunarli hisobot ko'rinishida ko'ra olishini ta'minlash.

---

## 🏛 Clean Architecture va Qatlamlar Qoidasi

Ushbu funksional loyihaning qat'iy **Clean Architecture** qoidalariga muvofiq 3 ta bosqichda amalga oshiriladi:

1. **1-qadam (DB Qatlami - Repozitoriy):** `AdminRepository` ga barcha mentorlar va shogirdlari bo'yicha jamlangan SQL so'rov metodi.
2. **2-qadam (Logika Qatlami - Servis):** `MentorService` ga hisob-kitob, tartiblash va xatolarsiz formatlash mantiqi.
3. **3-qadam (Taqdimot Qatlami - Bot):** `menu_kb.py` da yangi alohida Reply tugma va `statistics.py` da hisobot handleri.

---

## 📝 Bosqichma-bosqich O'zgarishlar

### 1. 🗄️ Ma'lumotlar Bazasi Qatlami (`db/repositories/`)
- **Fayl:** `BilimGo/db/repositories/admin_repo.py`
- **Metod:** `get_mentors_infrastructure_usage_overview()`
- **Vazifasi:**
  - `license_nodes`, `users` (mentorlar), `cabinets`, `ai_token_usage` va `server_expense_usage` jadvallarini birlashtirib:
    - Har bir mentorning ismi, ID raqami, telefoni, o'quvchilari soni;
    - 🤖 AI Tyutor: jami savollar, jami tokenlar (`prompt + completion`) va jami AI summasi;
    - 🖥 Server yuki: jami video streamlar (`units_used`), hosting va jami server summasi;
    - 💰 Jami yuk summasi (AI + Server);
  - Butun platforma bo'yicha Grand Total (umumiy yig'indi) ma'lumotlarini hisoblab beradi.

---

### 2. 🧠 Biznes Mantiq Qatlami (`services/`)
- **Fayl:** `BilimGo/services/mentor_service.py`
- **Metod:** `get_mentors_infrastructure_usage()`
- **Vazifasi:**
  - Repozitoriydan olingan ma'lumotlarni tekshiradi;
  - Mentorlarni eng ko'p resurs/token ishlatganiga qarab yuqoridan pastga saralaydi;
  - Sonlar, valyuta (`so'm`) va tokenlarni formatlaydi.

---

### 3. 🤖 Telegram Bot Qatlami (`bot/`)
- **Fayl 1:** `BilimGo/bot/keyboards/admin/menu_kb.py`
  - `ADMIN_MENU` Reply klaviaturasiga yangi alohida tugma qo'shiladi:
    `KeyboardButton(text="⚡️ Server yuki va AI tokenlar")`
- **Fayl 2:** `BilimGo/bot/handlers/admin/statistics.py`
  - Handler: `F.text.in_(["⚡️ Server yuki va AI tokenlar", "🖥 Server yuki va AI tokenlar", "/infra_stats"])`
  - Super admin ekanligini tasdiqlab, chiroyli va qulay Telegram hisoboti ko'rinishida chiqaradi.

---

## 🧪 Tekshirish va Sinov Rejasi

1. **Python skript orqali test:**
   - DB so'rovi va servis metodini test qilib, xatosiz ishlayotganini tasdiqlash.
2. **Sintaksis tekshiruvi:**
   - O'zgartirilgan barcha Python fayllarini kompilatsiya qilib tekshirish.
3. **Qo'lda tekshirish:**
   - Super admin botida menyu ko'rinishi va tugma bosilganda chiqadigan hisobot to'g'riligini tasdiqlash.
