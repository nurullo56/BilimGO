CREATE TABLE IF NOT EXISTS course_waitlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_course_waitlist_course ON course_waitlist(course_id);
CREATE INDEX IF NOT EXISTS idx_course_waitlist_user ON course_waitlist(user_id);

INSERT OR IGNORE INTO courses (id, title, description, owner_node_id, base_price, status)
VALUES (
    6,
    'Sun''iy Intellekt (AI) Asoslari',
    'ChatGPT, Prompts, AI agentlar, Midjourney va biznes jarayonlarini avtomatlashtirish bo‘yicha to‘liq amaliy kurs. Tez kunda!',
    1,
    0,
    'coming_soon'
);
