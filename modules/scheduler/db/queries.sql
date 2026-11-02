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
       created_at
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
