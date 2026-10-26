-- ChinaSeller PRO (course_id = 5) tariflarini qo'shish (agar kurs bazada mavjud bo'lsa)
CREATE TABLE IF NOT EXISTS course_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    tier_code TEXT NOT NULL CHECK (tier_code IN ('start', 'pro', 'vip')),
    name TEXT NOT NULL,
    price REAL NOT NULL,
    tagline TEXT,
    features TEXT NOT NULL,
    is_popular INTEGER NOT NULL DEFAULT 0,
    has_chat INTEGER NOT NULL DEFAULT 0,
    has_live INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(course_id, tier_code)
);

CREATE INDEX IF NOT EXISTS idx_course_tariffs_course ON course_tariffs(course_id);

ALTER TABLE lessons ADD COLUMN required_tier TEXT DEFAULT 'start';
ALTER TABLE access_grants ADD COLUMN tier TEXT DEFAULT 'start';
ALTER TABLE sales ADD COLUMN tier TEXT DEFAULT 'start';

INSERT OR IGNORE INTO course_tariffs (course_id, tier_code, name, price, tagline, features, is_popular, has_chat, has_live)
SELECT 5, 'start', 'START', 220000, 'Mustaqil o‘rganuvchilar', '["Xitoy saytlari (Pinduoduo, 1688, Taobao) darslari", "WeChat + 250 ta ta’minotchi bazasi", "Instagram va Telegram ochish bo‘yicha baza"]', 0, 0, 0
WHERE EXISTS (SELECT 1 FROM courses WHERE id = 5);

INSERT OR IGNORE INTO course_tariffs (course_id, tier_code, name, price, tagline, features, is_popular, has_chat, has_live)
SELECT 5, 'pro', 'PRO (Tavsiya etiladi)', 550000, 'Tizimli savdo va avtomatika xohlovchilar', '["Barcha Start darslari", "5 ta sinovdan o‘tgan targetolog kontakti", "AI avto-javob & lid yig‘ish darsi/skripti", "Taplink & Uzum Market darslari"]', 1, 1, 1
WHERE EXISTS (SELECT 1 FROM courses WHERE id = 5);

INSERT OR IGNORE INTO course_tariffs (course_id, tier_code, name, price, tagline, features, is_popular, has_chat, has_live)
SELECT 5, 'vip', 'VIP / INDIVIDUAL', 1200000, 'Shaxsiy natija va tayyor tizim', '["Barcha Pro imkoniyatlari", "Birinchi buyurtmani birgalikda amalga oshirish", "AI bot/tizimni shaxsan sozlab berish bo‘yicha yordam", "Yakkama-yakka konsultatsiya"]', 0, 1, 1
WHERE EXISTS (SELECT 1 FROM courses WHERE id = 5);

UPDATE lessons SET required_tier = 'start' WHERE id = 50;
UPDATE lessons SET required_tier = 'start' WHERE id = 51;
UPDATE lessons SET required_tier = 'pro' WHERE id = 52;
UPDATE lessons SET required_tier = 'vip' WHERE id = 53;
