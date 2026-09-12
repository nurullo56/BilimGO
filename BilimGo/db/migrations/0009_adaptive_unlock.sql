CREATE TABLE IF NOT EXISTS unlock_tier_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    min_score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    daily_lesson_limit INTEGER,
    label TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_unlock_tier_rules_course ON unlock_tier_rules(course_id);

CREATE TABLE IF NOT EXISTS daily_unlock_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    plan_date TEXT NOT NULL,
    max_lessons_allowed INTEGER,
    comprehension_score_basis INTEGER,
    status TEXT NOT NULL DEFAULT 'unlocked' CHECK (status IN ('locked', 'unlocked', 'completed')),
    UNIQUE (student_id, course_id, plan_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_unlock_plan_lookup ON daily_unlock_plan(student_id, course_id, plan_date);

-- Global standart tier'lar (course_id = NULL). Kurs bo'yicha override qilish uchun
-- xuddi shu min_score/max_score oralig'ida course_id ko'rsatilgan qator qo'shiladi.
INSERT INTO unlock_tier_rules (course_id, min_score, max_score, daily_lesson_limit, label) VALUES
    (NULL, 75, 100, NULL, 'Yuqori'),
    (NULL, 60, 74, 6, 'Ortacha'),
    (NULL, 40, 59, 3, 'Past'),
    (NULL, 0, 39, 1, 'Juda past');
