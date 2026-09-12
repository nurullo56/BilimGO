CREATE TABLE IF NOT EXISTS cabinets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_node_id INTEGER NOT NULL UNIQUE REFERENCES license_nodes(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    branding_config TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cabinet_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cabinet_id INTEGER NOT NULL REFERENCES cabinets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_in_cabinet TEXT NOT NULL CHECK (role_in_cabinet IN ('mentor', 'student')),
    joined_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cabinet_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_cabinet_members_user ON cabinet_members(user_id);

CREATE TABLE IF NOT EXISTS chat_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cabinet_id INTEGER NOT NULL REFERENCES cabinets(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cabinet_id, course_id)
);

CREATE TABLE IF NOT EXISTS chat_room_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_read_message_id INTEGER,
    UNIQUE (room_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_room_members_user ON chat_room_members(user_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_room_time ON chat_messages(room_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room_id_desc ON chat_messages(room_id, id);
