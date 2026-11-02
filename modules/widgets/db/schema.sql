-- A dashboard widget. numeric shows the last value; chart shows the last
-- `points` values as a sparkline; button calls its configured hook.
CREATE TABLE IF NOT EXISTS widgets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    kind             TEXT NOT NULL DEFAULT 'numeric',
    source_kind      TEXT NOT NULL DEFAULT 'manual',
    source           TEXT,
    method           TEXT NOT NULL DEFAULT 'GET',
    unit             TEXT,
    points           INTEGER NOT NULL DEFAULT 24,
    created_epoch    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS widget_values (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    widget_id        INTEGER NOT NULL REFERENCES widgets(id),
    value_text       TEXT NOT NULL,
    value_milli      INTEGER NOT NULL DEFAULT 0,
    recorded_epoch   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS widget_values_widget ON widget_values(widget_id);
