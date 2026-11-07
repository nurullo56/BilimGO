-- Kurslarning qisqacha tavsif (description) matnlarini to'ldirish
UPDATE courses 
SET description = '1688, Taobao, zavodlardan tovar xarid qilish, kargo logistikasi, bojxona va O''zbekistonda yuqori marja bilan sotish bo''yicha to''liq amaliy kurs.'
WHERE id = 5 AND (description IS NULL OR description = '');

UPDATE courses 
SET description = 'Veb-saytlar yaratish, Google AdSense, Yandex Direct, SEO va internet monetizatsiyasi orqali passiv daromad topish bo''yicha to''liq amaliy kurs.'
WHERE id = 4 AND (description IS NULL OR description = '');
