CREATE TABLE IF NOT EXISTS tariff_quotas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL REFERENCES license_nodes(id) ON DELETE CASCADE,
    tariff_name TEXT NOT NULL CHECK (tariff_name IN ('standart', 'pro', 'vip')),
    course_title TEXT NOT NULL,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    total_quota INTEGER NOT NULL,
    used_quota INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(node_id, course_title)
);

CREATE INDEX IF NOT EXISTS idx_tariff_quotas_node ON tariff_quotas(node_id);
