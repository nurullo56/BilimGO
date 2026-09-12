CREATE TABLE IF NOT EXISTS server_expense_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expense_type TEXT NOT NULL CHECK (expense_type IN ('video_bandwidth', 'active_student', 'hosting_maintenance', 'api_request')),
    units_used REAL NOT NULL DEFAULT 1.0,
    unit_name TEXT NOT NULL DEFAULT 'view',
    cost_sum REAL NOT NULL DEFAULT 0.0,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_server_expense_mentor ON server_expense_usage(mentor_id);
CREATE INDEX IF NOT EXISTS idx_server_expense_type ON server_expense_usage(expense_type);
