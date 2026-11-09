-- name: insert_widget
INSERT INTO widgets (title, kind, source_kind, source, method, unit, points, position, size, decimals, created_epoch)
VALUES (:title, :kind, :source_kind, :source, :method, :unit, :points, :position, :size, :decimals, :created_epoch);

-- name: list_widgets
SELECT id, title, kind, source_kind, COALESCE(source, '') AS source,
       method, COALESCE(unit, '') AS unit, points, position, size, decimals, pinned, created_epoch
FROM widgets ORDER BY position, title;

-- name: update_widget
UPDATE widgets SET title = :title, kind = :kind, source_kind = :source_kind,
    source = :source, method = :method, unit = :unit, points = :points, decimals = :decimals WHERE id = :id;

-- name: move_widget
UPDATE widgets SET position = :position WHERE id = :id;

-- name: resize_widget
UPDATE widgets SET size = :size WHERE id = :id;

-- name: pin_widget
UPDATE widgets SET pinned = :pinned WHERE id = :id;

-- name: delete_widget
DELETE FROM widgets WHERE id = :id;

-- name: insert_widget_value
INSERT INTO widget_values (widget_id, value_text, value_milli, recorded_epoch)
VALUES (:widget_id, :value_text, :value_milli, :recorded_epoch);

-- name: list_widget_values
SELECT * FROM widget_values WHERE widget_id = :widget_id
ORDER BY recorded_epoch DESC, id DESC LIMIT 100;

-- name: latest_widget_value
SELECT id, widget_id, value_text, value_milli, recorded_epoch
FROM widget_values WHERE widget_id = :widget_id
ORDER BY recorded_epoch DESC, id DESC LIMIT 1;
