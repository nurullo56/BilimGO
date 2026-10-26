-- Dars testlari (savollar va javob variantlari)
 CREATE TABLE IF NOT EXISTS lesson_quizzes (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
     question TEXT NOT NULL,
     options TEXT NOT NULL, -- JSON array: masalan ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]
     correct_option_index INTEGER NOT NULL, -- 0, 1, 2 yoki 3
     explanation TEXT DEFAULT '',
     created_by TEXT NOT NULL DEFAULT 'admin' CHECK (created_by IN ('admin', 'ai', 'super_mentor')),
     created_at TEXT NOT NULL DEFAULT (datetime('now'))
 );
 
 CREATE INDEX IF NOT EXISTS idx_lesson_quizzes_lesson ON lesson_quizzes(lesson_id);
 
 -- O'quvchilarning test topshirish tarixi
 CREATE TABLE IF NOT EXISTS lesson_quiz_submissions (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
     quiz_id INTEGER NOT NULL REFERENCES lesson_quizzes(id) ON DELETE CASCADE,
     selected_option_index INTEGER NOT NULL,
     is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
     submitted_at TEXT NOT NULL DEFAULT (datetime('now'))
 );
 
 CREATE INDEX IF NOT EXISTS idx_quiz_subs_user_lesson ON lesson_quiz_submissions(user_id, lesson_id);
 
 -- O'quvchi dars testini muvaffaqiyatli topshirganligi va keyingi darsni ochish huquqi
 CREATE TABLE IF NOT EXISTS lesson_completions (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
     quiz_passed INTEGER NOT NULL DEFAULT 1 CHECK (quiz_passed IN (0, 1)),
     completed_at TEXT NOT NULL DEFAULT (datetime('now')),
     UNIQUE (user_id, lesson_id)
 );
 
 CREATE INDEX IF NOT EXISTS idx_lesson_completions_user_lesson ON lesson_completions(user_id, lesson_id);
