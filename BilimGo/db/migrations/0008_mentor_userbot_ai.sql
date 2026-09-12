CREATE TABLE IF NOT EXISTS mentor_userbots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    session_string TEXT,
    phone_number TEXT,
    status TEXT NOT NULL DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected', 'error')),
    connected_at TEXT
);

CREATE TABLE IF NOT EXISTS lesson_assessment_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL UNIQUE REFERENCES lessons(id) ON DELETE CASCADE,
    key_concepts TEXT NOT NULL,
    min_pass_score INTEGER NOT NULL DEFAULT 70
);

CREATE TABLE IF NOT EXISTS comprehension_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    mentor_userbot_id INTEGER REFERENCES mentor_userbots(id) ON DELETE SET NULL,
    check_type TEXT NOT NULL DEFAULT 'freeform_chat' CHECK (
        check_type IN ('quiz', 'freeform_chat', 'voice_reply')
    ),
    raw_response TEXT NOT NULL,
    score INTEGER,
    ai_reasoning TEXT,
    ai_model_used TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'evaluated', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    evaluated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_comprehension_checks_status ON comprehension_checks(status);
CREATE INDEX IF NOT EXISTS idx_comprehension_checks_student ON comprehension_checks(student_id, lesson_id, created_at);
