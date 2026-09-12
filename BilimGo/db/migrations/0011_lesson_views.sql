CREATE TABLE IF NOT EXISTS lesson_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    delivery_token_id INTEGER REFERENCES delivery_tokens(id) ON DELETE SET NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    watch_duration_sec INTEGER NOT NULL DEFAULT 0,
    completion_percent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_lesson_views_lesson_user ON lesson_views(lesson_id, user_id);
CREATE INDEX IF NOT EXISTS idx_lesson_views_user_time ON lesson_views(user_id, started_at);
