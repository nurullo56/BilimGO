CREATE TABLE IF NOT EXISTS mentor_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('payme', 'click')),
    card_token TEXT NOT NULL,
    card_number_masked TEXT,
    card_expire TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(mentor_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_mentor_cards_mentor ON mentor_cards(mentor_id, is_active);

CREATE TABLE IF NOT EXISTS royalty_auto_settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL REFERENCES license_nodes(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    sales_count INTEGER NOT NULL,
    provider TEXT NOT NULL,
    external_txn_id TEXT,
    status TEXT NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_royalty_auto_settlements_node ON royalty_auto_settlements(node_id);
