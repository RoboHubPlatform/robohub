-- name: insert_category
INSERT INTO categories (name) VALUES (:name);

-- name: list_categories
SELECT id, name, kind, capabilities, uses, origin FROM categories ORDER BY name;

-- name: seed_category
INSERT OR IGNORE INTO categories (name, kind, capabilities, uses, origin)
VALUES (:name, :kind, :capabilities, :uses, 'preset');

-- name: update_category_preset
UPDATE categories SET kind = :kind, capabilities = :capabilities, uses = :uses, origin = 'preset'
WHERE name = :name;

-- name: insert_item
INSERT INTO items (name, category_id, unit, quantity_milli, reorder_milli,
                   location, notes, kind, handle)
VALUES (:name, NULLIF(:category_id, ''), :unit, :quantity_milli,
        :reorder_milli, :location, :notes, :kind, :handle);

-- name: list_items
SELECT i.id, i.name, COALESCE(c.name, '') AS category, i.category_id, i.unit,
       i.quantity_milli, i.reorder_milli, COALESCE(i.location, '') AS location,
       COALESCE(i.notes, '') AS notes, i.kind, i.handle, i.runtime_s, i.runtime_at,
       i.portion_milli, COALESCE(c.capabilities, '') AS capabilities,
       COALESCE(c.uses, '') AS uses
FROM items i
LEFT JOIN categories c ON c.id = i.category_id
ORDER BY i.name;

-- One item, by what names it: looked up, not found in a list of every item.
-- name: get_item_by_handle
SELECT i.id, i.name, COALESCE(c.name, '') AS category, i.category_id, i.unit,
       i.quantity_milli, i.reorder_milli, COALESCE(i.location, '') AS location,
       COALESCE(i.notes, '') AS notes, i.kind, i.handle, i.runtime_s, i.runtime_at,
       i.portion_milli, COALESCE(c.capabilities, '') AS capabilities,
       COALESCE(c.uses, '') AS uses
FROM items i
LEFT JOIN categories c ON c.id = i.category_id
WHERE i.handle = :handle AND i.handle <> ''
LIMIT 1;

-- name: get_item_by_id
SELECT i.id, i.name, COALESCE(c.name, '') AS category, i.category_id, i.unit,
       i.quantity_milli, i.reorder_milli, COALESCE(i.location, '') AS location,
       COALESCE(i.notes, '') AS notes, i.kind, i.handle, i.runtime_s, i.runtime_at,
       i.portion_milli, COALESCE(c.capabilities, '') AS capabilities,
       COALESCE(c.uses, '') AS uses
FROM items i
LEFT JOIN categories c ON c.id = i.category_id
WHERE i.id = :id
LIMIT 1;

-- name: update_item_details
UPDATE items
SET name = :name, category_id = NULLIF(:category_id, ''), unit = :unit,
    reorder_milli = :reorder_milli, location = :location, notes = :notes,
    kind = :kind, handle = :handle, portion_milli = :portion_milli
WHERE id = :id;

-- name: set_item_runtime
UPDATE items SET runtime_s = :runtime_s, runtime_at = :runtime_at WHERE id = :id;

-- name: update_item_stock
UPDATE items SET quantity_milli = quantity_milli + :delta WHERE id = :id;

-- name: insert_expense
INSERT INTO expenses
    (item_id, item, category_id, quantity_milli, unit_price_cents, total_cents,
     source, purchased_at, comment)
VALUES
    (NULLIF(:item_id, ''), :item, NULLIF(:category_id, ''), :quantity_milli,
     :unit_price_cents, :total_cents, :source, :purchased_at, :comment);

-- name: list_expenses
SELECT e.id, e.item, COALESCE(c.name, '') AS category,
       e.quantity_milli, e.unit_price_cents, e.total_cents,
       COALESCE(e.source, '') AS source, e.purchased_at,
       COALESCE(e.comment, '') AS comment
FROM expenses e
LEFT JOIN categories c ON c.id = e.category_id
ORDER BY e.purchased_at DESC, e.id DESC;

-- name: delete_expense
DELETE FROM expenses WHERE id = :id;

-- name: total_expenses
SELECT COALESCE(SUM(total_cents), 0) AS total_cents FROM expenses;

-- name: insert_movement
INSERT INTO stock_movements
    (item_id, kind, quantity_milli, unit_price_cents, total_cents, source,
     occurred_at, comment)
VALUES
    (:item_id, :kind, :quantity_milli, :unit_price_cents, :total_cents, :source,
     :occurred_at, :comment);

-- name: low_stock_items
SELECT i.id, i.name, i.quantity_milli, i.reorder_milli, i.unit,
       COALESCE(i.location, '') AS location
FROM items i
WHERE i.reorder_milli > 0 AND i.quantity_milli <= i.reorder_milli
ORDER BY i.quantity_milli;

-- name: list_bindings
SELECT b.item_id, b.capability, b.source, b.access, b.bound_at, i.handle, i.name
FROM item_bindings b
JOIN items i ON i.id = b.item_id
ORDER BY i.name, b.capability;

-- The source one capability of one item is bound to.
-- name: get_binding
SELECT b.source FROM item_bindings b
WHERE b.item_id = :item_id AND b.capability = :capability;

-- name: bind_capability
INSERT OR REPLACE INTO item_bindings (item_id, capability, source, access)
VALUES (:item_id, :capability, :source, :access);

-- name: unbind_capability
DELETE FROM item_bindings WHERE item_id = :item_id AND capability = :capability;

-- name: set_item_handle
UPDATE items SET handle = :handle WHERE id = :id;

-- name: clear_item_handle
UPDATE items SET handle = '' WHERE handle = :handle AND id <> :id;

-- A category a person added, renamed; a preset's name is the application's.
-- name: rename_category
UPDATE categories SET name = :name WHERE id = :id AND origin = 'person';

-- A category a person added, deleted while no item is in it; purchases that
-- named it keep their amounts.
-- name: delete_category
DELETE FROM categories WHERE id = :id AND origin = 'person'
  AND NOT EXISTS (SELECT 1 FROM items WHERE items.category_id = categories.id);

-- name: detach_category_expenses
UPDATE expenses SET category_id = NULL WHERE category_id = :category_id;

-- An item deleted: its bindings and stock history go with it; its purchases
-- stay in the expenses, no longer naming it.
-- name: delete_item_bindings
DELETE FROM item_bindings WHERE item_id = :item_id;

-- name: delete_item_movements
DELETE FROM stock_movements WHERE item_id = :item_id;

-- name: detach_item_expenses
UPDATE expenses SET item_id = NULL WHERE item_id = :item_id;

-- name: delete_item
DELETE FROM items WHERE id = :id;
