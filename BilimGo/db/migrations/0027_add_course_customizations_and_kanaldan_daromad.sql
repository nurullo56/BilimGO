-- 0027_add_course_customizations_and_kanaldan_daromad.sql
-- Kurslar jadvaliga rasm, maxsus e'lon va dastur rejasi ustunlarini qo'shish

ALTER TABLE courses ADD COLUMN image_url TEXT;
ALTER TABLE courses ADD COLUMN notice_text TEXT;
ALTER TABLE courses ADD COLUMN syllabus TEXT;

