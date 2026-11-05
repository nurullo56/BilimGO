# 🛠️ Yangi Reja: "Kanaldan Daromad" Kursi, Dinamik E'lonlar, Kurs Rasmlari va Waitlist Tizimi

Ushbu hujjat loyihada yangi **"Kanaldan Daromad"** kursini kiritish, kurs rasmlari va tavsif ostidagi maxsus chegirma e'lonlarini dinamik boshqarish hamda Waitlist bildirishnomalarini to'liq moslashtirish bo'yicha tuzildi.

---

## 🎯 1. Maqsad va Vazifalar

1. **Yangi Kurs — «Kanaldan Daromad»:**
   - Platformadagi mavjud 6 ta kurs qatoriga 7-kurs sifatida «Kanaldan Daromad» kursini kiritish.
   - U darhol katalogda, Telegram botda va WebAppda o'z o'rnini egallaydi.
2. **Kurs Rasmlarini Yangilash (`image_url`):**
   - Hozirgi kunda bazada kurs rasmlari ustuni yo'q (frontend faqat umumiy Unsplash linklariga bog'langan).
   - `courses` jadvaliga `image_url` ustuni qo'shiladi va admin istalgan paytda har bir kursning rasmini o'zgartira oladi.
3. **Maxsus Chegirma / E'lon Bloki (`notice_text`):**
   - `image.png` dagi qizil strelka bilan ko'rsatilganidek, kurs tavsifi ostida dastlabki 30–40 nafar o'quvchiga mo'ljallangan chegirma xabari bloki paydo bo'ladi (*«🔥 Dastlabki 30 ta o'quvchiga 50% chegirmada qabul ochildi!»*).
   - Admin buni istalgan vaqtda kurs chiqqandan keyin ham yangilab tura oladi.
4. **Kutilayotgan Dastur Rejasini Dinamik Qilish:**
   - `Gemini_Generated_Image...jpg` da ko'ringanidek, frontenddagi qotirib qo'yilgan AI darslari olib tashlanadi.
   - Har bir kurs o'zining mustaqil rejasiga ega bo'ladi (ChinaSeller PRO ga AI darslari aralashib ketmaydi).
5. **Waitlist Xabarlarini Dinamik Qilish:**
   - Talaba qaysi kursga navbatga yozilsa, unga aynan o'sha kursning nomi bilan shaxsiy bot xabarnomasi va Mini App bildirishnomasi yuboriladi.

---

## 🗄️ 2. Ma'lumotlar Bazasi Qatlami (DB Layer)

### [NEW] `BilimGo/db/migrations/0027_add_course_customizations_and_kanaldan_daromad.sql`
```sql
-- 1. Kurslar jadvaliga rasm, e'lon matni va dastur rejasi ustunlarini qo'shish
ALTER TABLE courses ADD COLUMN image_url TEXT;
ALTER TABLE courses ADD COLUMN notice_text TEXT;
ALTER TABLE courses ADD COLUMN syllabus TEXT;

-- 2. Yangi "Kanaldan Daromad" kursini qo'shish
INSERT INTO courses (id, title, description, owner_node_id, base_price, status, is_waitlist, notice_text, image_url)
VALUES (
    7,
    'Kanaldan Daromad',
    'Telegram kanallar ochish, ularni tezkor rivojlantirish, auditoriya yig''ish va reklama orqali muntazam daromadga chiqish bo''yicha amaliy kurs.',
    1,
    490000,
    'published',
    1,
    '🔥 Dastlabki 30 ta o''quvchiga 50% chegirmada qabul ochildi!',
    'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&auto=format&fit=crop&q=60'
);
```

### [MODIFY] `BilimGo/db/repositories/course_repo.py`
- `Course` modeliga `image_url: str | None = None`, `notice_text: str | None = None`, `syllabus: str | None = None` maydonlarini qo'shish.
- `update_notice_text(course_id: int, notice_text: str)` metodini kiritish.
- `update_image_url(course_id: int, image_url: str)` metodini kiritish.

---

## ⚙️ 3. Biznes Servislar Qatlami (Services Layer)

### [MODIFY] `BilimGo/services/course_service.py`
- Kurslar ro'yxati va detali olinganda `image_url`, `notice_text` va `syllabus` ni to'liq qaytarish.
- `set_course_notice(course_id, text)` va `set_course_image(course_id, url)` boshqaruv metodlarini ulash.

---

## 🌐 4. Backend Web API Qatlami (Web API Layer)

### [MODIFY] `BilimGo/web/routers/waitlist.py`
- `join_course_waitlist` da `course_repo.get_by_id(course_id)` orqali haqiqiy kurs nomini olish:
  - Mini App bildirishnomasi: `f"{course.title} Navbatiga yozildingiz! 🎉"`
  - Shaxsiy Telegram xabarnomasi: `f"Hurmatli <b>{user_name}</b>, siz <b>{course.title}</b> kursi kutish ro'yxatiga muvaffaqiyatli qo'shildingiz!"`
  - Admin guruhiga bildirishnoma: `f"📋 Yangi o'quvchi <b>{course.title}</b> navbatiga yozildi!"`

### [MODIFY] `BilimGo/web/routers/player.py`
- `/api/courses` va `/api/courses/{id}` endpointlarida har bir kurs obyektiga `image_url`, `notice_text` va `syllabus` parametrlarini qo'shib uzatish.

---

## 💻 5. Frontend WebApp Qatlami (UI Layer)

### [MODIFY] `frontend/src/types.ts`
- `Course` interfeysiga `image_url?: string; notice_text?: string; syllabus?: any[];` maydonlarini qo'shish.

### [MODIFY] `frontend/src/services/api.ts`
- `enhanceCourse` funksiyasida `c.image_url` mavjud bo'lsa, uni asosiy rasm (`thumbnail`) sifatida olish.
- Yangi kurs «Kanaldan Daromad» uchun toifa (`Telegram Kanallar & Daromad`) va parametrlar belgilash.

### [MODIFY] `frontend/src/components/CourseDetailView.tsx`
- **Maxsus Chegirma / E'lon Bloki:** Kurs tavsifi ostida:
  ```tsx
  {course.notice_text && (
    <div className="p-3.5 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center gap-3">
      <Sparkles className="w-5 h-5 text-amber-500 shrink-0" />
      <span className="text-xs sm:text-sm font-semibold text-amber-700 dark:text-amber-300">
        {course.notice_text}
      </span>
    </div>
  )}
  ```
- **Kutilayotgan Dastur Rejasi:** Qotirilgan AI darslarini olib tashlash va har bir kursning o'ziga xos modul rejasi ko'rinishini ta'minlash.

### [MODIFY] `frontend/src/components/CatalogView.tsx`
- Kurs kartochkalarida `course.image_url || course.thumbnail` orqali yangilangan rasmlarni aks ettirish.

---

## 🤖 6. Bot Admin Qatlami (Telegram Bot Layer)

### [MODIFY] `BilimGo/bot/handlers/admin/course_waitlist.py`
- Yangi «Kanaldan Daromad» kursi boshqaruv panelida darhol paydo bo'ladi va admin uni bir zumda Waitlist yoki Sotuv rejimiga o'tkaza oladi.

---

## 🧪 7. Sinov va Tekshirish (Verification)
1. `database.run_migrations` orqali `0027` migratsiyasini qo'llash va yangi kurs bazaga yozilganini tekshirish.
2. `pytest` orqali butun tizim testlarini yashil holatga keltirish.
3. `frontend` papkasida `npm run build` orqali yangi WebApp paketini yig'ish.
4. `python run_all.py` orqali barcha 5 ta servis xatolarsiz ishga tushishini tasdiqlash.
