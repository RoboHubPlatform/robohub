-- The rules module's tables. They belong to the module: an application that
-- includes it gets them generated in (rho-sql 0.2), and never repeats them.

-- A rule: when `when_expr` holds (for for_s seconds, when set), run do_actions;
-- when it stops holding — or, with clear_expr, when that holds — run
-- else_actions. A rule fires at most once per cooldown_s. origin is preset (from
-- the application's presets, kept current by them) or person. state is idle,
-- pending or active; state_since and last_fired are Unix seconds.
CREATE TABLE IF NOT EXISTS rules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    enabled       INTEGER NOT NULL DEFAULT 1,
    when_expr     TEXT NOT NULL,
    clear_expr    TEXT NOT NULL DEFAULT '',
    for_s         INTEGER NOT NULL DEFAULT 0,
    cooldown_s    INTEGER NOT NULL DEFAULT 0,
    do_actions    TEXT NOT NULL DEFAULT '',
    else_actions  TEXT NOT NULL DEFAULT '',
    origin        TEXT NOT NULL DEFAULT 'person',
    state         TEXT NOT NULL DEFAULT 'idle',
    state_since   INTEGER NOT NULL DEFAULT 0,
    last_fired    INTEGER NOT NULL DEFAULT 0,
    last_error    TEXT NOT NULL DEFAULT ''
);

-- What the presets say each preset rule is, kept as they say it: a rule a person
-- edited (origin 'edited') is no longer changed by the presets, and is put back
-- from here when they ask for the preset again.
CREATE TABLE IF NOT EXISTS rule_presets (
    name          TEXT PRIMARY KEY,
    when_expr     TEXT NOT NULL,
    clear_expr    TEXT NOT NULL DEFAULT '',
    for_s         INTEGER NOT NULL DEFAULT 0,
    cooldown_s    INTEGER NOT NULL DEFAULT 0,
    do_actions    TEXT NOT NULL DEFAULT '',
    else_actions  TEXT NOT NULL DEFAULT ''
);

-- A mode: a named change for a while. Starting it runs do_actions and
-- suspends the rules named in suspends (comma-separated); it ends after
-- duration_s (0: when someone ends it) and runs end_actions.
CREATE TABLE IF NOT EXISTS rule_modes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL DEFAULT '',
    duration_s   INTEGER NOT NULL DEFAULT 0,
    do_actions   TEXT NOT NULL DEFAULT '',
    end_actions  TEXT NOT NULL DEFAULT '',
    suspends     TEXT NOT NULL DEFAULT '',
    origin       TEXT NOT NULL DEFAULT 'person'
);

-- The mode in force, at most one: the row with id 1, or none.
CREATE TABLE IF NOT EXISTS rule_mode_active (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    started_at  INTEGER NOT NULL,
    ends_at     INTEGER NOT NULL DEFAULT 0,
    actor       TEXT NOT NULL DEFAULT ''
);
