-- A chore definition and its next due time. next_due_epoch is Unix seconds;
-- zero means the schedule has no wall-clock due time (a usage chore).
CREATE TABLE IF NOT EXISTS chores (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    title                  TEXT NOT NULL,
    description            TEXT,
    schedule_kind          TEXT NOT NULL,
    schedule_value         TEXT,
    interval_hours         INTEGER NOT NULL DEFAULT 0,
    usage_interval_hours   INTEGER NOT NULL DEFAULT 0,
    usage_accum_seconds    INTEGER NOT NULL DEFAULT 0,
    grace_hours            INTEGER NOT NULL DEFAULT 0,
    priority               TEXT NOT NULL DEFAULT 'normal',
    enabled                INTEGER NOT NULL DEFAULT 1,
    next_due_epoch         INTEGER NOT NULL DEFAULT 0,
    snoozed_until_epoch    INTEGER NOT NULL DEFAULT 0,
    last_completed_epoch   INTEGER NOT NULL DEFAULT 0,
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    runtime_of             TEXT NOT NULL DEFAULT '',
    runtime_seen           INTEGER NOT NULL DEFAULT 0,
    consumes               TEXT NOT NULL DEFAULT '',
    consumes_milli         INTEGER NOT NULL DEFAULT 0
);

-- runtime_of names an inventory item (by handle) whose switch runtime drives a
-- usage chore, instead of hours typed in; runtime_seen is the item's runtime
-- already counted. consumes names an item a completion takes consumes_milli
-- (thousandths) off: a filter pad, a dose.
ALTER TABLE chores ADD COLUMN runtime_of TEXT NOT NULL DEFAULT '';
ALTER TABLE chores ADD COLUMN runtime_seen INTEGER NOT NULL DEFAULT 0;
ALTER TABLE chores ADD COLUMN consumes TEXT NOT NULL DEFAULT '';
ALTER TABLE chores ADD COLUMN consumes_milli INTEGER NOT NULL DEFAULT 0;

-- One completion of a chore, with the note a person left.
CREATE TABLE IF NOT EXISTS chore_completions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id          INTEGER NOT NULL REFERENCES chores(id),
    completed_epoch   INTEGER NOT NULL,
    note              TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS chore_completions_chore ON chore_completions(chore_id);
