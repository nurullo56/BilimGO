CREATE TABLE IF NOT EXISTS ai_token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_sum REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ai_token_mentor ON ai_token_usage(mentor_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_student ON ai_token_usage(student_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_lesson ON ai_token_usage(lesson_id);
