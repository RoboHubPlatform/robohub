-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    level       TEXT NOT NULL DEFAULT 'info',
    message     TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL,
    dismissed   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS notifications_active
    ON notifications(dismissed, expires_at);
