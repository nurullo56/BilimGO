-- 0028_add_course_instructor.sql
-- Kurslar jadvaliga o'qituvchi/mentor ismi uchun ustun qo'shish
ALTER TABLE courses ADD COLUMN instructor TEXT;
