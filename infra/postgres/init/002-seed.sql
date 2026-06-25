INSERT INTO users (id, username, account_status, profile_img, created_at) VALUES
    (7, 'demo-user-07', 'active', 'avatars/demo-07.png', '2026-06-24T01:00:00Z'),
    (18, 'demo-user-18', 'locked', 'avatars/demo-18.png', '2026-06-24T01:05:00Z'),
    (42, 'demo-user-42', 'active', NULL, '2026-06-24T01:10:00Z'),
    (88, 'demo-user-88', 'disabled', 'avatars/demo-88.png', '2026-06-24T01:15:00Z');

INSERT INTO orders (id, user_id, status, total_cents, created_at) VALUES
    (1001, 7, 'paid', 2599, '2026-06-24T01:20:00Z'),
    (1002, 18, 'cancelled', 4900, '2026-06-24T01:25:00Z'),
    (1003, 42, 'paid', 1299, '2026-06-24T01:30:00Z'),
    (1004, 42, 'pending', 7599, '2026-06-24T01:35:00Z'),
    (1005, 88, 'refunded', 3499, '2026-06-24T01:40:00Z');

INSERT INTO login_events (id, user_id, outcome, source_ip, occurred_at) VALUES
    (2001, 7, 'success', '192.0.2.7', '2026-06-24T02:10:00Z'),
    (2002, 18, 'failure', '192.0.2.18', '2026-06-24T02:15:00Z'),
    (2003, 42, 'success', '192.0.2.42', '2026-06-24T02:20:00Z'),
    (2004, 42, 'success', '192.0.2.42', '2026-06-24T02:30:00Z'),
    (2005, 88, 'failure', '192.0.2.88', '2026-06-24T02:35:00Z');

INSERT INTO error_events (id, request_id, user_id, service_name, error_type, message, occurred_at) VALUES
    (3001, 'req-demo-4201', 42, 'ProfileService', 'NullPointerException', 'profile_img was null while rendering avatar', '2026-06-24T02:40:00Z'),
    (3002, 'req-demo-4202', 42, 'ProfileService', 'NullPointerException', 'profile_img was null while rendering avatar', '2026-06-24T02:45:00Z'),
    (3003, 'req-demo-4203', 42, 'ProfileService', 'NullPointerException', 'profile_img was null while rendering avatar', '2026-06-24T02:50:00Z');
