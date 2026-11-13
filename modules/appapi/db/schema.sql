-- The appapi module's tables. They belong to the module: an application that
-- includes it gets them generated in (rho-sql 0.2), and never repeats them.

-- A value the application offers. kind is derived (from its presets), published
-- (computed by the application) or export (a reading it passes on). updated_at
-- is Unix seconds.
CREATE TABLE IF NOT EXISTS appapi_values (
    id          TEXT PRIMARY KEY,
    value       TEXT NOT NULL DEFAULT '',
    unit        TEXT NOT NULL DEFAULT '',
    label       TEXT NOT NULL DEFAULT '',
    kind        TEXT NOT NULL DEFAULT 'published',
    updated_at  INTEGER NOT NULL DEFAULT 0
);

-- Each value's history, one row per change, kept for 30 days. at is Unix
-- seconds; value is the number, when the value is one.
CREATE TABLE IF NOT EXISTS appapi_history (
    id     TEXT NOT NULL,
    at     INTEGER NOT NULL,
    value  REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS appapi_history_id_at ON appapi_history(id, at);

-- How a value is derived, from the application's presets. source is what it is
-- derived from (an inventory item's capability, `heater.temperature`, or a
-- journal kind for `since`); fn is latest, avg, min, max, integral, since or
-- export; window_s is the window avg/min/max/integral look over.
CREATE TABLE IF NOT EXISTS appapi_derived (
    id        TEXT PRIMARY KEY,
    source    TEXT NOT NULL,
    fn        TEXT NOT NULL DEFAULT 'latest',
    window_s  INTEGER NOT NULL DEFAULT 0,
    unit      TEXT NOT NULL DEFAULT '',
    label     TEXT NOT NULL DEFAULT ''
);
