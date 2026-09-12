CREATE TABLE IF NOT EXISTS completion_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    notified_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'failed')),
    UNIQUE(user_id, lesson_id)
);

CREATE INDEX IF NOT EXISTS idx_completion_notifications_user_lesson ON completion_notifications(user_id, lesson_id);
