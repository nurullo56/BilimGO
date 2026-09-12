CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    license_node_id INTEGER NOT NULL REFERENCES license_nodes(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    payment_provider TEXT NOT NULL CHECK (payment_provider IN ('click', 'payme')),
    payment_status TEXT NOT NULL DEFAULT 'pending' CHECK (
        payment_status IN ('pending', 'paid', 'failed', 'refunded')
    ),
    external_txn_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    paid_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_student ON sales(student_id);
CREATE INDEX IF NOT EXISTS idx_sales_node_status ON sales(license_node_id, payment_status);

CREATE TABLE IF NOT EXISTS royalty_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    node_id INTEGER NOT NULL REFERENCES license_nodes(id) ON DELETE CASCADE,
    percent_applied REAL NOT NULL,
    amount REAL NOT NULL,
    settled_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_royalty_ledger_sale ON royalty_ledger(sale_id);
CREATE INDEX IF NOT EXISTS idx_royalty_ledger_node_settled ON royalty_ledger(node_id, settled_at);

CREATE TABLE IF NOT EXISTS click_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    click_trans_id TEXT NOT NULL UNIQUE,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    prepare_id TEXT,
    amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'prepared' CHECK (status IN ('prepared', 'confirmed', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payme_transactions (
    id TEXT PRIMARY KEY,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    state INTEGER NOT NULL DEFAULT 1,
    create_time INTEGER NOT NULL,
    perform_time INTEGER NOT NULL DEFAULT 0,
    cancel_time INTEGER NOT NULL DEFAULT 0,
    reason INTEGER
);

CREATE INDEX IF NOT EXISTS idx_payme_transactions_sale ON payme_transactions(sale_id);
