-- 0029_assign_chinaseller_mentor.sql
-- ChinaSeller PRO (id=5) kursi uchun Bosh mentor Sayyora (Safinzadas) ni biriktirish

-- 1. Sayyora (Safinzadas) foydalanuvchisini yaratish (agar kurs mavjud bo'lsa)
INSERT OR IGNORE INTO users (telegram_id, full_name, role, status)
SELECT 8486162906, 'Sayyora (Safinzadas)', 'mentor', 'active'
WHERE EXISTS (SELECT 1 FROM courses WHERE id = 5);

UPDATE users
SET role = 'mentor', full_name = 'Sayyora (Safinzadas)', status = 'active'
WHERE telegram_id = 8486162906;

-- 2. Sayyora uchun ChinaSeller PRO (course_id = 5) bo'yicha litsenziya tugunini yaratish (agar kurs mavjud bo'lsa)
INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status)
SELECT 
    (SELECT id FROM license_nodes ORDER BY id ASC LIMIT 1), 
    u.id, 
    5, 
    0.0, 
    'independent', 
    'active'
FROM users u 
WHERE u.telegram_id = 8486162906
AND EXISTS (SELECT 1 FROM courses WHERE id = 5)
AND NOT EXISTS (
    SELECT 1 FROM license_nodes ln WHERE ln.owner_user_id = u.id AND ln.course_id = 5
);

-- 3. ChinaSeller PRO (course_id = 5) kursining egasini (owner_node_id) va instruktorini yangilash
UPDATE courses
SET 
    instructor = 'Sayyora (Safinzadas) - Xitoy bo''yicha ekspert (Bosh Mentor)',
    owner_node_id = COALESCE(
        (
            SELECT ln.id FROM license_nodes ln 
            JOIN users u ON u.id = ln.owner_user_id 
            WHERE u.telegram_id = 8486162906 AND ln.course_id = 5
            ORDER BY ln.id DESC LIMIT 1
        ),
        owner_node_id
    )
WHERE id = 5;

-- 4. Mentor uchun o'quv kabineti yaratish
INSERT INTO cabinets (owner_node_id, display_name)
SELECT ln.id, 'Sayyora (Safinzadas)''s kabineti'
FROM license_nodes ln
JOIN users u ON u.id = ln.owner_user_id
WHERE u.telegram_id = 8486162906 AND ln.course_id = 5
AND NOT EXISTS (
    SELECT 1 FROM cabinets c WHERE c.owner_node_id = ln.id
);

-- 5. Mentorni o'z kabinetiga a'zo qilish
INSERT INTO cabinet_members (cabinet_id, user_id, role_in_cabinet)
SELECT c.id, u.id, 'mentor'
FROM cabinets c
JOIN license_nodes ln ON ln.id = c.owner_node_id
JOIN users u ON u.id = ln.owner_user_id
WHERE u.telegram_id = 8486162906 AND ln.course_id = 5
AND NOT EXISTS (
    SELECT 1 FROM cabinet_members cm WHERE cm.cabinet_id = c.id AND cm.user_id = u.id
);

-- 6. Kurs bo'yicha chat xonasi yaratish
INSERT INTO chat_rooms (cabinet_id, course_id)
SELECT c.id, 5
FROM cabinets c
JOIN license_nodes ln ON ln.id = c.owner_node_id
JOIN users u ON u.id = ln.owner_user_id
WHERE u.telegram_id = 8486162906 AND ln.course_id = 5
AND EXISTS (SELECT 1 FROM courses WHERE id = 5)
AND NOT EXISTS (
    SELECT 1 FROM chat_rooms cr WHERE cr.cabinet_id = c.id AND cr.course_id = 5
);

-- 7. Mentorni kurs chat xonasiga a'zo qilish
INSERT INTO chat_room_members (room_id, user_id)
SELECT cr.id, u.id
FROM chat_rooms cr
JOIN cabinets c ON c.id = cr.cabinet_id
JOIN license_nodes ln ON ln.id = c.owner_node_id
JOIN users u ON u.id = ln.owner_user_id
WHERE u.telegram_id = 8486162906 AND ln.course_id = 5
AND NOT EXISTS (
    SELECT 1 FROM chat_room_members crm WHERE crm.room_id = cr.id AND crm.user_id = u.id
);

-- 8. Mentorga kursga to'liq kirish huquqini (access_grants) ochish
INSERT OR IGNORE INTO access_grants (user_id, course_id, granted_via_sale_id, status)
SELECT u.id, 5, 0, 'active'
FROM users u 
WHERE u.telegram_id = 8486162906
AND EXISTS (SELECT 1 FROM courses WHERE id = 5);
