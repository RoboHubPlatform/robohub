-- name: insert_journal_entry
INSERT INTO journal_entries (at, level, kind, subject, actor, message)
VALUES (:at, :level, :kind, :subject, :actor, :message);

-- name: list_journal_entries
SELECT id, at, level, kind, subject, actor, message, resolved_at
FROM journal_entries
WHERE at >= :since
  AND (:level = '' OR level = :level)
  AND (:kind = '' OR kind = :kind)
ORDER BY at DESC, id DESC
LIMIT 500;

-- name: list_open_journal_entries
SELECT id, at, level, kind, subject, actor, message, resolved_at
FROM journal_entries
WHERE resolved_at = 0 AND level <> 'info'
ORDER BY at DESC, id DESC
LIMIT 500;

-- name: resolve_journal_entry
UPDATE journal_entries SET resolved_at = :resolved_at WHERE id = :id AND resolved_at = 0;

-- name: prune_journal_entries
DELETE FROM journal_entries WHERE at < :before AND (resolved_at > 0 OR level = 'info');

-- name: last_journal_entry
SELECT id, at, level, kind, subject, actor, message, resolved_at
FROM journal_entries
WHERE kind = :kind AND (:subject = '' OR subject = :subject)
ORDER BY at DESC, id DESC
LIMIT 1;

-- name: count_open_journal_entries
-- How many entries are still open, counted rather than read: the badge is not
-- capped at the rows a page reads.
SELECT COUNT(*) AS entries FROM journal_entries WHERE resolved_at = 0 AND level <> 'info';
