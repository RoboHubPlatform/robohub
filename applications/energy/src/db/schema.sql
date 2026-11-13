-- The appapi module's tables.
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


-- The inventory module's tables.
-- The inventory module's tables. They belong to the module: an application
-- that includes it gets them generated in (rho-sql 0.2), and never repeats them.
--
-- A column added in a later version is in its table's CREATE and in an ALTER
-- after it: a new database gets it from the CREATE (the ALTER then finds it and
-- is passed over), an older one from the ALTER.

-- The categories an item or a purchase can belong to. An application seeds its
-- own from its presets. kind is what an item in it is by default: consumable
-- (used up: food, fertiliser), part (fitted and replaced: filter media) or
-- equipment (installed, and possibly automated). capabilities are what an
-- equipment item in it can be bound to — `switch, power?` — a trailing ? marks
-- one that may stay unbound. uses names a category whose items it consumes
-- (a feeder uses food).
CREATE TABLE IF NOT EXISTS categories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,
    kind         TEXT NOT NULL DEFAULT 'consumable',
    capabilities TEXT NOT NULL DEFAULT '',
    uses         TEXT NOT NULL DEFAULT ''
);

ALTER TABLE categories ADD COLUMN kind TEXT NOT NULL DEFAULT 'consumable';
ALTER TABLE categories ADD COLUMN capabilities TEXT NOT NULL DEFAULT '';
ALTER TABLE categories ADD COLUMN uses TEXT NOT NULL DEFAULT '';

-- What is on hand, how much of it, and when to reorder.
CREATE TABLE IF NOT EXISTS items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    category_id      INTEGER REFERENCES categories(id),
    unit             TEXT NOT NULL DEFAULT 'unit',
    quantity_milli   INTEGER NOT NULL DEFAULT 0,
    reorder_milli    INTEGER NOT NULL DEFAULT 0,
    location         TEXT,
    notes            TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    kind             TEXT NOT NULL DEFAULT 'consumable',
    handle           TEXT NOT NULL DEFAULT '',
    runtime_s        INTEGER NOT NULL DEFAULT 0,
    runtime_at       INTEGER NOT NULL DEFAULT 0,
    portion_milli    INTEGER NOT NULL DEFAULT 0
);

-- kind: consumable, part or equipment. handle is the name everything else uses
-- for the item — `filter-main` — so a rule, a dashboard card or a chore names the
-- item and never the plug it happens to be on. runtime_s is how long its switch
-- has been on, counted from its history up to runtime_at (Unix seconds).
-- portion_milli is what one use takes from the category it uses (a feeder's
-- portion of food).
ALTER TABLE items ADD COLUMN kind TEXT NOT NULL DEFAULT 'consumable';
ALTER TABLE items ADD COLUMN handle TEXT NOT NULL DEFAULT '';
ALTER TABLE items ADD COLUMN runtime_s INTEGER NOT NULL DEFAULT 0;
ALTER TABLE items ADD COLUMN runtime_at INTEGER NOT NULL DEFAULT 0;
ALTER TABLE items ADD COLUMN portion_milli INTEGER NOT NULL DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS items_handle ON items(handle) WHERE handle <> '';

-- What an equipment item's capabilities are bound to: one gateway source each.
-- access is control for a capability the item drives (a switch) and read for one
-- it only reports (power, temperature). A source is controlled by one item at
-- most, so two items cannot fight over one relay.
CREATE TABLE IF NOT EXISTS item_bindings (
    item_id     INTEGER NOT NULL REFERENCES items(id),
    capability  TEXT NOT NULL,
    source      TEXT NOT NULL,
    access      TEXT NOT NULL DEFAULT 'read',
    bound_at    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (item_id, capability)
);

CREATE UNIQUE INDEX IF NOT EXISTS item_bindings_control ON item_bindings(source) WHERE access = 'control';

-- One purchase line. Money is integer cents and quantity is thousandths, so a
-- total never depends on the floating-point spelling of 12.34.
CREATE TABLE IF NOT EXISTS expenses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id           INTEGER REFERENCES items(id),
    item              TEXT NOT NULL,
    category_id       INTEGER REFERENCES categories(id),
    quantity_milli    INTEGER NOT NULL DEFAULT 1000,
    unit_price_cents  INTEGER NOT NULL DEFAULT 0,
    total_cents       INTEGER NOT NULL DEFAULT 0,
    source            TEXT,
    purchased_at      TEXT NOT NULL,
    comment           TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS expenses_purchased_at ON expenses(purchased_at);

-- Every change to the stock, so the quantity can be read as a history rather
-- than only as a current number. quantity_milli is signed: negative is stock
-- leaving the shelf.
CREATE TABLE IF NOT EXISTS stock_movements (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id          INTEGER NOT NULL REFERENCES items(id),
    kind             TEXT NOT NULL,
    quantity_milli   INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL DEFAULT 0,
    total_cents      INTEGER NOT NULL DEFAULT 0,
    source           TEXT,
    occurred_at      TEXT NOT NULL,
    comment          TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS stock_movements_item ON stock_movements(item_id);


-- The journal module's tables.
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


-- The scheduler module's tables.
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


-- The widgets module's tables.
-- A dashboard widget. numeric shows the last value; chart shows the last
-- `points` values as a sparkline; status shows a badge with an ok/warn/bad/info
-- state; button calls its configured hook; toggle reflects and sets a switch.
--
-- `position`, `size`, `decimals` and `pinned` are part of the card layout. The
-- canonical definition lives here; a host includes this file's tables in its
-- own SQL port so the module and the host cannot describe two different
-- widgets tables.
CREATE TABLE IF NOT EXISTS widgets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    kind             TEXT NOT NULL DEFAULT 'numeric',
    source_kind      TEXT NOT NULL DEFAULT 'manual',
    source           TEXT,
    method           TEXT NOT NULL DEFAULT 'GET',
    unit             TEXT,
    points           INTEGER NOT NULL DEFAULT 24,
    position         INTEGER NOT NULL DEFAULT 0,
    size             TEXT NOT NULL DEFAULT 'small',
    decimals         INTEGER NOT NULL DEFAULT 2,
    pinned           INTEGER NOT NULL DEFAULT 0,
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


-- The energy application's store.
--
-- Measured values are integers in one stated unit, never floating point: a
-- watt is a watt, a volt is millivolts, an ampere is milliamperes, a
-- temperature is milli-Celsius and a state of charge is thousandths of a
-- percent. The unit is part of the column name, so a reading cannot be read in
-- the wrong scale by accident.
--
-- There is no telemetry here. Mesh owns telemetry: the readings energy produces
-- leave through its outbox and are stored once, in Mesh; the readings it shows
-- come back through Mesh's API.

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
PRAGMA journal_size_limit=16777216;
PRAGMA wal_autocheckpoint=512;
PRAGMA auto_vacuum=INCREMENTAL;

-- A generation line: a PV string, a microinverter or a wind turbine. The driver
-- contract is the same for all three; `kind` says which curve and which
-- electrical window applies.
CREATE TABLE IF NOT EXISTS energy_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL DEFAULT 'solar_pv',
    bus             TEXT NOT NULL DEFAULT '',
    address         TEXT NOT NULL DEFAULT '',
    mesh_source     TEXT NOT NULL DEFAULT '',
    rated_w         INTEGER NOT NULL DEFAULT 0,
    power_w         INTEGER NOT NULL DEFAULT 0,
    voltage_mv      INTEGER NOT NULL DEFAULT 0,
    current_ma      INTEGER NOT NULL DEFAULT 0,
    temperature_mc  INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'online',
    protocol        TEXT NOT NULL DEFAULT '',
    updated_epoch   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS energy_sources_kind ON energy_sources(kind);

-- One LiFePO4 bank. The cell figures are the ones a BMS reports for the whole
-- bank: the lowest and the highest cell, so the delta is visible without a
-- per-cell table that a bank of sixteen cells would make noisy.
CREATE TABLE IF NOT EXISTS energy_batteries (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,
    chemistry          TEXT NOT NULL DEFAULT 'LiFePO4',
    capacity_wh        INTEGER NOT NULL DEFAULT 0,
    soc_milli          INTEGER NOT NULL DEFAULT 0,
    soh_milli          INTEGER NOT NULL DEFAULT 100000,
    voltage_mv         INTEGER NOT NULL DEFAULT 0,
    current_ma         INTEGER NOT NULL DEFAULT 0,
    temperature_mc     INTEGER NOT NULL DEFAULT 0,
    cell_min_mv        INTEGER NOT NULL DEFAULT 0,
    cell_max_mv        INTEGER NOT NULL DEFAULT 0,
    charge_limit_ma    INTEGER NOT NULL DEFAULT 0,
    discharge_limit_ma INTEGER NOT NULL DEFAULT 0,
    can_profile        TEXT NOT NULL DEFAULT 'L51',
    bms_host           TEXT NOT NULL DEFAULT '',
    mesh_source        TEXT NOT NULL DEFAULT '',
    status             TEXT NOT NULL DEFAULT 'online',
    updated_epoch      INTEGER NOT NULL DEFAULT 0
);

-- The utility connection. `import_w` and `export_w` are both non-negative; a
-- sign is a direction and the two directions are two figures.
CREATE TABLE IF NOT EXISTS energy_grids (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    utility         TEXT NOT NULL DEFAULT '',
    mesh_source     TEXT NOT NULL DEFAULT '',
    phases          INTEGER NOT NULL DEFAULT 1,
    voltage_mv      INTEGER NOT NULL DEFAULT 0,
    frequency_mhz   INTEGER NOT NULL DEFAULT 0,
    import_w        INTEGER NOT NULL DEFAULT 0,
    export_w        INTEGER NOT NULL DEFAULT 0,
    import_limit_w  INTEGER NOT NULL DEFAULT 0,
    export_limit_w  INTEGER NOT NULL DEFAULT 0,
    zero_export     INTEGER NOT NULL DEFAULT 1,
    synchronized    INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'online',
    updated_epoch   INTEGER NOT NULL DEFAULT 0
);

-- A load, and whether the site may shed it. Priority 1 is life safety and is
-- never shed; priority 3 is the discretionary load a low battery turns off
-- first.
CREATE TABLE IF NOT EXISTS energy_loads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    zone            TEXT NOT NULL DEFAULT 'site',
    priority        INTEGER NOT NULL DEFAULT 2,
    power_w         INTEGER NOT NULL DEFAULT 0,
    critical        INTEGER NOT NULL DEFAULT 0,
    shed            INTEGER NOT NULL DEFAULT 0,
    state           TEXT NOT NULL DEFAULT 'on',
    updated_epoch   INTEGER NOT NULL DEFAULT 0
);

-- One row: the site's policy. Thresholds are stored in the same scaled units as
-- the readings, so a comparison is an integer comparison and a form can be
-- validated before it reaches this table.
CREATE TABLE IF NOT EXISTS energy_config (
    id                        INTEGER PRIMARY KEY CHECK (id = 1),
    mode                      TEXT NOT NULL DEFAULT 'hybrid',
    grid_forming              INTEGER NOT NULL DEFAULT 1,
    zero_export               INTEGER NOT NULL DEFAULT 1,
    peak_shaving              INTEGER NOT NULL DEFAULT 0,
    tariff_optimization       INTEGER NOT NULL DEFAULT 0,
    reserve_soc_milli         INTEGER NOT NULL DEFAULT 25000,
    load_shed_soc_milli       INTEGER NOT NULL DEFAULT 15000,
    generator_start_soc_milli INTEGER NOT NULL DEFAULT 10000,
    generator_stop_soc_milli  INTEGER NOT NULL DEFAULT 40000,
    charge_limit_ma           INTEGER NOT NULL DEFAULT 60000,
    discharge_limit_ma        INTEGER NOT NULL DEFAULT 120000,
    charge_voltage_mv         INTEGER NOT NULL DEFAULT 57600,
    discharge_cutoff_mv       INTEGER NOT NULL DEFAULT 44000,
    export_limit_w            INTEGER NOT NULL DEFAULT 0,
    solar_temp_limit_mc       INTEGER NOT NULL DEFAULT 75000,
    battery_temp_limit_mc     INTEGER NOT NULL DEFAULT 45000,
    source_over_voltage_mv    INTEGER NOT NULL DEFAULT 600000,
    source_over_current_ma    INTEGER NOT NULL DEFAULT 20000,
    battery_cell_delta_mv     INTEGER NOT NULL DEFAULT 200,
    grid_min_voltage_mv       INTEGER NOT NULL DEFAULT 207000,
    grid_max_voltage_mv       INTEGER NOT NULL DEFAULT 253000,
    grid_min_frequency_mhz    INTEGER NOT NULL DEFAULT 49500,
    grid_max_frequency_mhz    INTEGER NOT NULL DEFAULT 50500,
    generator                 INTEGER NOT NULL DEFAULT 0,
    load_shed                 INTEGER NOT NULL DEFAULT 0,
    tariff_peak               INTEGER NOT NULL DEFAULT 0,
    sim_fault                 TEXT NOT NULL DEFAULT '',
    sim_tick                  INTEGER NOT NULL DEFAULT 0,
    energy_today_wh           INTEGER NOT NULL DEFAULT 0,
    energy_total_wh           INTEGER NOT NULL DEFAULT 0,
    updated_epoch             INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO energy_config (id) VALUES (1);

-- The transition state of every safety rule. A fault is recorded on the edge
-- into the bad condition, not on every tick of it, so a dashboard shows one
-- badge for one condition and a clear when it ends.
CREATE TABLE IF NOT EXISTS energy_fault_state (
    code           TEXT PRIMARY KEY,
    active         INTEGER NOT NULL DEFAULT 0,
    severity       TEXT NOT NULL DEFAULT 'ERROR',
    message        TEXT NOT NULL DEFAULT '',
    updated_epoch  INTEGER NOT NULL DEFAULT 0
);

-- Append-only audit trail: modes, manual overrides, generator starts, faults.
CREATE TABLE IF NOT EXISTS energy_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    severity        TEXT NOT NULL DEFAULT 'INFO',
    kind            TEXT NOT NULL,
    message         TEXT NOT NULL,
    created_epoch   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS energy_events_created ON energy_events(created_epoch);

-- --------------------------------------------------------------------------
-- inventory module schema (canonical: modules/inventory/db/schema.sql)
-- --------------------------------------------------------------------------

-- The categories an item or a purchase can belong to.
CREATE TABLE IF NOT EXISTS categories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE
);

-- What is on hand, how much of it, and when to reorder.
CREATE TABLE IF NOT EXISTS items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    category_id      INTEGER REFERENCES categories(id),
    unit             TEXT NOT NULL DEFAULT 'unit',
    quantity_milli   INTEGER NOT NULL DEFAULT 0,
    reorder_milli    INTEGER NOT NULL DEFAULT 0,
    location         TEXT,
    notes            TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One purchase line. Money is integer cents and quantity is thousandths, so a
-- total never depends on the floating-point spelling of 12.34.
CREATE TABLE IF NOT EXISTS expenses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id           INTEGER REFERENCES items(id),
    item              TEXT NOT NULL,
    category_id       INTEGER REFERENCES categories(id),
    quantity_milli    INTEGER NOT NULL DEFAULT 1000,
    unit_price_cents  INTEGER NOT NULL DEFAULT 0,
    total_cents       INTEGER NOT NULL DEFAULT 0,
    source            TEXT,
    purchased_at      TEXT NOT NULL,
    comment           TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS expenses_purchased_at ON expenses(purchased_at);

-- Every change to the stock, so the quantity can be read as a history rather
-- than only as a current number. quantity_milli is signed: negative is stock
-- leaving the shelf.
CREATE TABLE IF NOT EXISTS stock_movements (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id          INTEGER NOT NULL REFERENCES items(id),
    kind             TEXT NOT NULL,
    quantity_milli   INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL DEFAULT 0,
    total_cents      INTEGER NOT NULL DEFAULT 0,
    source           TEXT,
    occurred_at      TEXT NOT NULL,
    comment          TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS stock_movements_item ON stock_movements(item_id);

-- --------------------------------------------------------------------------
-- scheduler module schema (canonical: modules/scheduler/db/schema.sql)
-- --------------------------------------------------------------------------

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
    created_at             TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One completion of a chore, with the note a person left.
CREATE TABLE IF NOT EXISTS chore_completions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id          INTEGER NOT NULL REFERENCES chores(id),
    completed_epoch   INTEGER NOT NULL,
    note              TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS chore_completions_chore ON chore_completions(chore_id);

-- --------------------------------------------------------------------------
-- widgets module schema (canonical: modules/widgets/db/schema.sql)
-- --------------------------------------------------------------------------

-- A dashboard widget. numeric shows the last value; chart shows the last
-- `points` values as a sparkline; status shows a badge with an ok/warn/bad/info
-- state; button calls its configured hook; toggle reflects and sets a switch.
--
-- `position`, `size`, `decimals` and `pinned` are part of the card layout. The
-- canonical definition lives here; a host includes this file's tables in its
-- own SQL port so the module and the host cannot describe two different
-- widgets tables.
CREATE TABLE IF NOT EXISTS widgets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    kind             TEXT NOT NULL DEFAULT 'numeric',
    source_kind      TEXT NOT NULL DEFAULT 'manual',
    source           TEXT,
    method           TEXT NOT NULL DEFAULT 'GET',
    unit             TEXT,
    points           INTEGER NOT NULL DEFAULT 24,
    position         INTEGER NOT NULL DEFAULT 0,
    size             TEXT NOT NULL DEFAULT 'small',
    decimals         INTEGER NOT NULL DEFAULT 2,
    pinned           INTEGER NOT NULL DEFAULT 0,
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
