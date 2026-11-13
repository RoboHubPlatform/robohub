-- name: list_appapi_values
SELECT id, value, unit, label, kind, updated_at FROM appapi_values ORDER BY id;

-- name: put_appapi_value
INSERT OR REPLACE INTO appapi_values (id, value, unit, label, kind, updated_at)
VALUES (:id, :value, :unit, :label, :kind, :updated_at);

-- name: add_appapi_point
INSERT INTO appapi_history (id, at, value) VALUES (:id, :at, :value);

-- name: list_appapi_points
SELECT at, value FROM appapi_history
WHERE id = :id AND at >= :since AND at <= :until
ORDER BY at
LIMIT 5000;

-- name: prune_appapi_points
DELETE FROM appapi_history WHERE at < :before;

-- name: list_appapi_derived
SELECT id, source, fn, window_s, unit, label FROM appapi_derived ORDER BY id;

-- name: put_appapi_derived
INSERT OR REPLACE INTO appapi_derived (id, source, fn, window_s, unit, label)
VALUES (:id, :source, :fn, :window_s, :unit, :label);
