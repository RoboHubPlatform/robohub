-- name: insert_chore
INSERT INTO chores
    (title, description, schedule_kind, schedule_value, interval_hours,
     usage_interval_hours, grace_hours, priority, next_due_epoch, enabled)
VALUES
    (:title, :description, :schedule_kind, :schedule_value, :interval_hours,
     :usage_interval_hours, :grace_hours, :priority, :next_due_epoch, :enabled);

-- name: list_chores
SELECT id, title, COALESCE(description, '') AS description, schedule_kind,
       COALESCE(schedule_value, '') AS schedule_value, interval_hours,
       usage_interval_hours, usage_accum_seconds, grace_hours, priority,
       enabled, next_due_epoch, snoozed_until_epoch, last_completed_epoch,
       created_at, runtime_of, runtime_seen, consumes, consumes_milli
FROM chores
ORDER BY enabled DESC, next_due_epoch, title;

-- name: complete_chore
UPDATE chores
SET next_due_epoch = :next_due_epoch,
    last_completed_epoch = :last_completed_epoch,
    snoozed_until_epoch = 0,
    usage_accum_seconds = :usage_accum_seconds
WHERE id = :id;

-- name: insert_completion
INSERT INTO chore_completions (chore_id, completed_epoch, note)
VALUES (:chore_id, :completed_epoch, :note);

-- name: snooze_chore
UPDATE chores SET snoozed_until_epoch = :snoozed_until_epoch WHERE id = :id;

-- name: add_usage
UPDATE chores
SET usage_accum_seconds = usage_accum_seconds + :delta_seconds
WHERE id = :id;

-- name: list_completions
SELECT c.id, c.chore_id, ch.title, c.completed_epoch,
       COALESCE(c.note, '') AS note
FROM chore_completions c
LEFT JOIN chores ch ON ch.id = c.chore_id
ORDER BY c.completed_epoch DESC, c.id DESC
LIMIT 50;

-- name: set_chore_links
UPDATE chores SET runtime_of = :runtime_of, consumes = :consumes, consumes_milli = :consumes_milli
WHERE id = (SELECT MAX(id) FROM chores WHERE title = :title);

-- name: set_chore_runtime_seen
UPDATE chores SET runtime_seen = :runtime_seen WHERE id = :id;

-- name: seed_chore
INSERT INTO chores
    (title, description, schedule_kind, schedule_value, interval_hours,
     usage_interval_hours, grace_hours, priority, next_due_epoch, enabled)
SELECT :title, :description, :schedule_kind, :schedule_value, :interval_hours,
       :usage_interval_hours, :grace_hours, :priority, :next_due_epoch, 1
WHERE NOT EXISTS (SELECT 1 FROM chores WHERE title = :title);

-- A chore changed by a person: what it is, when it comes round, what it uses.
-- name: update_chore
UPDATE chores SET title = :title, description = :description, schedule_kind = :schedule_kind,
    schedule_value = :schedule_value, interval_hours = :interval_hours,
    usage_interval_hours = :usage_interval_hours, grace_hours = :grace_hours,
    priority = :priority, next_due_epoch = :next_due_epoch, runtime_of = :runtime_of,
    consumes = :consumes, consumes_milli = :consumes_milli
WHERE id = :id;

-- A chore deleted, and its history with it.
-- name: delete_chore_completions
DELETE FROM chore_completions WHERE chore_id = :chore_id;

-- name: delete_chore
DELETE FROM chores WHERE id = :id;
