CREATE TABLE IF NOT EXISTS student_feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL DEFAULT 5,
    category TEXT NOT NULL DEFAULT 'general',
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_student_feedbacks_user ON student_feedbacks(user_id);
CREATE INDEX IF NOT EXISTS idx_student_feedbacks_course ON student_feedbacks(course_id);
CREATE INDEX IF NOT EXISTS idx_student_feedbacks_created ON student_feedbacks(created_at);
