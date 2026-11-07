# 📋 Dars Ko'rish Sahifasini Tozalash Rejasi (VideoPlayerView)

Ushbu reja foydalanuvchi talablari asosida dars ko'rish ekranidagi takroriy va ortiqcha elementlarni xavfsiz va aniq tozalashni ko'zda tutadi.

---

## 🎯 Maqsad va O'zgarishlar Mazmuni

1. **Audio pleyer ichidagi takrorlangan dars nomini olib tashlash:**
   - Audio pleyer ichidagi takroriy `<h3>{currentLesson?.title}</h3>` sarlavhasi olib tashlanadi (chunki pleyer ostidagi asosiy dars bloki ichida dars nomi to'liq ko'rsatiladi). Faqat `OVOZLI DARS & INFOGRAFIKA` belgisi va tezlik (`1x`) tugmasi qoldiriladi.

2. **Takroriy "← Kursga qaytish" tugmasini olib tashlash:**
   - Ekranning eng yuqori qismidagi Navbar'da allaqachon orqaga qaytuvchi `← Bilim GO` tugmasi mavjud.
   - Pleyer tepasida joylashgan ikkinchi `← Kursga qaytish` tugmasi ortiqcha bo'lgani sababli olib tashlanadi.

3. **"Video / Ovozli" almashtirish tugmasini olib tashlash:**
   - Tizim dars turini (video yoki audio) avtomatik aniqlaydi (`isAudio`).
   - Qo'lda almashtirish tugmasi (`forceMode`) foydalanuvchiga kerak emas va ortiqcha bo'lgani sababli olib tashlanadi.
