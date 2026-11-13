-- The journal module's table. It belongs to the module: an application that
-- includes it gets it generated in (rho-sql 0.2), and never repeats it.

-- One thing that happened. at is Unix seconds. level is info, warning or error.
-- kind is what sort of thing it was (switch, rule, mode, test, stock, system),
-- subject what it was about (an item's handle, a rule's name), actor who or what
-- did it (person:ana, rule:keep-temperature, device, system). An entry that
-- needs attention stays open until resolved_at is set.
CREATE TABLE IF NOT EXISTS journal_entries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    at           INTEGER NOT NULL,
    level        TEXT NOT NULL DEFAULT 'info',
    kind         TEXT NOT NULL DEFAULT 'system',
    subject      TEXT NOT NULL DEFAULT '',
    actor        TEXT NOT NULL DEFAULT 'system',
    message      TEXT NOT NULL,
    resolved_at  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS journal_entries_at ON journal_entries(at);
