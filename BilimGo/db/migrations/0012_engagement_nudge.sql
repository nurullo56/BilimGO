CREATE TABLE IF NOT EXISTS engagement_activity (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_lesson_completed_at TEXT
);

CREATE TABLE IF NOT EXISTS nudge_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trigger_reason TEXT NOT NULL DEFAULT 'inactive_24h',
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    current_step INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'stopped', 'exhausted'))
);

CREATE INDEX IF NOT EXISTS idx_nudge_campaigns_user_status ON nudge_campaigns(user_id, status);

CREATE TABLE IF NOT EXISTS nudge_messages_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES nudge_campaigns(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now'))
);
