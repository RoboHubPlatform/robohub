-- The energy application's store.
--
-- Measured values are integers in one stated unit, never floating point: a
-- watt is a watt, a volt is millivolts, an ampere is milliamperes, a
-- temperature is milli-Celsius and a state of charge is thousandths of a
-- percent. The unit is part of the column name, so a reading cannot be read in
-- the wrong scale by accident.
--
-- The telemetry tables at the end are the same ones Mesh and every other
-- telemetry consumer declare. The telemetry port writes them, so the schema is
-- applied to both the application database and the telemetry store, and the
-- store runs in WAL mode like the rest of the ecosystem.

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

-- The telemetry store. The telemetry port writes these, and the application
-- reads the fault table for its badges, so a power fault is visible to every
-- other telemetry consumer and survives the process that raised it.

CREATE TABLE IF NOT EXISTS telemetry_gateway (
    id          TEXT PRIMARY KEY,
    project     TEXT NOT NULL,
    url         TEXT NOT NULL,
    last_seq    INTEGER NOT NULL DEFAULT 0,
    updated_ms  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS telemetry_reading (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,
    gateway_id  TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    area_id     INTEGER NOT NULL,
    node_id     INTEGER NOT NULL,
    field       TEXT NOT NULL,
    value       REAL NOT NULL,
    status      INTEGER NOT NULL DEFAULT 0,
    received_ms INTEGER NOT NULL,
    UNIQUE(gateway_id, seq)
);

CREATE INDEX IF NOT EXISTS telemetry_reading_series
    ON telemetry_reading(project, area_id, node_id, field, received_ms);

CREATE INDEX IF NOT EXISTS telemetry_reading_time
    ON telemetry_reading(project, received_ms);

CREATE TABLE IF NOT EXISTS telemetry_latest (
    project     TEXT NOT NULL,
    area_id     INTEGER NOT NULL,
    node_id     INTEGER NOT NULL,
    field       TEXT NOT NULL,
    value       REAL NOT NULL,
    status      INTEGER NOT NULL DEFAULT 0,
    received_ms INTEGER NOT NULL,
    PRIMARY KEY (project, area_id, node_id, field)
);

CREATE TABLE IF NOT EXISTS telemetry_rollup_1m (
    project     TEXT NOT NULL,
    area_id     INTEGER NOT NULL,
    node_id     INTEGER NOT NULL,
    field       TEXT NOT NULL,
    bucket_ms   INTEGER NOT NULL,
    value_min   REAL NOT NULL,
    value_max   REAL NOT NULL,
    value_avg   REAL NOT NULL,
    samples     INTEGER NOT NULL,
    PRIMARY KEY (project, area_id, node_id, field, bucket_ms)
);

CREATE INDEX IF NOT EXISTS telemetry_rollup_1m_series
    ON telemetry_rollup_1m(project, area_id, node_id, field, bucket_ms);

CREATE INDEX IF NOT EXISTS telemetry_rollup_1m_time
    ON telemetry_rollup_1m(project, bucket_ms);

CREATE TABLE IF NOT EXISTS telemetry_rollup_1h (
    project     TEXT NOT NULL,
    area_id     INTEGER NOT NULL,
    node_id     INTEGER NOT NULL,
    field       TEXT NOT NULL,
    bucket_ms   INTEGER NOT NULL,
    value_min   REAL NOT NULL,
    value_max   REAL NOT NULL,
    value_avg   REAL NOT NULL,
    samples     INTEGER NOT NULL,
    PRIMARY KEY (project, area_id, node_id, field, bucket_ms)
);

CREATE INDEX IF NOT EXISTS telemetry_rollup_1h_series
    ON telemetry_rollup_1h(project, area_id, node_id, field, bucket_ms);

CREATE INDEX IF NOT EXISTS telemetry_rollup_1h_time
    ON telemetry_rollup_1h(project, bucket_ms);

CREATE TABLE IF NOT EXISTS telemetry_fault (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,
    gateway_id  TEXT NOT NULL DEFAULT '',
    area_id     INTEGER NOT NULL DEFAULT 0,
    node_id     INTEGER NOT NULL DEFAULT 0,
    field       TEXT NOT NULL,
    status      INTEGER NOT NULL,
    severity    TEXT NOT NULL,
    message     TEXT NOT NULL,
    created_ms  INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS telemetry_fault_time
    ON telemetry_fault(project, created_ms);

CREATE INDEX IF NOT EXISTS telemetry_fault_open
    ON telemetry_fault(project, severity, created_ms);

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
