CREATE TABLE IF NOT EXISTS delivery_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_delivery_tokens_hash ON delivery_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_delivery_tokens_user_lesson ON delivery_tokens(user_id, lesson_id);
