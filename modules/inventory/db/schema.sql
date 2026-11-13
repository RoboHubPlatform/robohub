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
