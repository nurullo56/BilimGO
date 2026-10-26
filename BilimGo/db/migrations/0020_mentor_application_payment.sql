-- Mentorlik arizalari jadvali va to'lov ma'lumotlari
CREATE TABLE IF NOT EXISTS mentor_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT,
    phone TEXT,
    telegram_username TEXT,
    course_direction TEXT,
    experience_bio TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    payment_amount INTEGER DEFAULT 949000,
    receipt_photo_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
