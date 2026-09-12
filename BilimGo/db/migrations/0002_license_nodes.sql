CREATE TABLE IF NOT EXISTS license_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER REFERENCES license_nodes(id) ON DELETE SET NULL,
    owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER,
    royalty_percent REAL NOT NULL DEFAULT 0,
    stage TEXT NOT NULL DEFAULT 'limit' CHECK (stage IN ('limit', 'hamkorlik', 'independent')),
    kpi_min_sales INTEGER NOT NULL DEFAULT 0,
    stage_started_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'terminated')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_license_nodes_parent ON license_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_license_nodes_owner ON license_nodes(owner_user_id);
