CREATE TABLE IF NOT EXISTS course_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('started', 'completed')),
    notified_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sending', 'sent', 'failed')),
    UNIQUE(user_id, course_id, notification_type)
);

CREATE INDEX IF NOT EXISTS idx_course_notifications_lookup 
ON course_notifications(user_id, course_id, notification_type);
