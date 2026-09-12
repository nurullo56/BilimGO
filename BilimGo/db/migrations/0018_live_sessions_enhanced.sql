ALTER TABLE live_sessions ADD COLUMN title TEXT;
ALTER TABLE live_sessions ADD COLUMN description TEXT;
ALTER TABLE live_sessions ADD COLUMN stream_key TEXT;
ALTER TABLE live_sessions ADD COLUMN viewer_count INTEGER DEFAULT 0;
ALTER TABLE live_sessions ADD COLUMN total_viewers INTEGER DEFAULT 0;
ALTER TABLE live_sessions ADD COLUMN started_at TEXT;
ALTER TABLE live_sessions ADD COLUMN ended_at TEXT;

CREATE TABLE IF NOT EXISTS live_polls (
    id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    options TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS live_poll_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id TEXT NOT NULL REFERENCES live_polls(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    option_index INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(poll_id, user_id)
);

CREATE TABLE IF NOT EXISTS live_questions (
    id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    answered INTEGER NOT NULL DEFAULT 0,
    answer TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS live_chat_messages (
    id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_live_polls_session ON live_polls(session_id);
CREATE INDEX IF NOT EXISTS idx_live_questions_session ON live_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_live_chat_session ON live_chat_messages(session_id, created_at);
