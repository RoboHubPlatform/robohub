-- name: list_rules_all
SELECT id, name, enabled, when_expr, clear_expr, for_s, cooldown_s, do_actions,
       else_actions, origin, state, state_since, last_fired, last_error
FROM rules ORDER BY name;

-- name: seed_rule
INSERT OR IGNORE INTO rules (name, when_expr, clear_expr, for_s, cooldown_s, do_actions, else_actions, origin)
VALUES (:name, :when_expr, :clear_expr, :for_s, :cooldown_s, :do_actions, :else_actions, :origin);

-- name: update_preset_rule
UPDATE rules SET when_expr = :when_expr, clear_expr = :clear_expr, for_s = :for_s,
    cooldown_s = :cooldown_s, do_actions = :do_actions, else_actions = :else_actions
WHERE name = :name AND origin = 'preset';

-- One rule, for its edit page.
-- name: get_rule
SELECT id, name, enabled, when_expr, clear_expr, for_s, cooldown_s, do_actions,
       else_actions, origin, state, state_since, last_fired, last_error
FROM rules WHERE id = :id;

-- A rule changed by a person. A preset rule becomes 'edited', which the presets
-- leave alone; its state starts again.
-- name: update_rule
UPDATE rules SET when_expr = :when_expr, clear_expr = :clear_expr, for_s = :for_s,
    cooldown_s = :cooldown_s, do_actions = :do_actions, else_actions = :else_actions,
    origin = CASE WHEN origin = 'preset' THEN 'edited' ELSE origin END,
    state = 'idle', last_error = ''
WHERE id = :id;

-- name: put_rule_preset
INSERT OR REPLACE INTO rule_presets (name, when_expr, clear_expr, for_s, cooldown_s, do_actions, else_actions)
VALUES (:name, :when_expr, :clear_expr, :for_s, :cooldown_s, :do_actions, :else_actions);

-- An edited preset rule put back as the presets say it.
-- name: reset_rule_to_preset
UPDATE rules SET
    when_expr = (SELECT p.when_expr FROM rule_presets p WHERE p.name = rules.name),
    clear_expr = (SELECT p.clear_expr FROM rule_presets p WHERE p.name = rules.name),
    for_s = (SELECT p.for_s FROM rule_presets p WHERE p.name = rules.name),
    cooldown_s = (SELECT p.cooldown_s FROM rule_presets p WHERE p.name = rules.name),
    do_actions = (SELECT p.do_actions FROM rule_presets p WHERE p.name = rules.name),
    else_actions = (SELECT p.else_actions FROM rule_presets p WHERE p.name = rules.name),
    origin = 'preset', state = 'idle', last_error = ''
WHERE id = :id AND origin = 'edited'
  AND EXISTS (SELECT 1 FROM rule_presets p WHERE p.name = rules.name);

-- name: set_rule_state
UPDATE rules SET state = :state, state_since = :state_since, last_fired = :last_fired,
    last_error = :last_error
WHERE id = :id;

-- name: set_rule_enabled
UPDATE rules SET enabled = :enabled WHERE id = :id;

-- name: delete_person_rule
DELETE FROM rules WHERE id = :id AND origin = 'person';

-- name: list_rule_modes
SELECT id, name, title, duration_s, do_actions, end_actions, suspends, origin
FROM rule_modes ORDER BY name;

-- name: seed_rule_mode
INSERT OR IGNORE INTO rule_modes (name, title, duration_s, do_actions, end_actions, suspends, origin)
VALUES (:name, :title, :duration_s, :do_actions, :end_actions, :suspends, 'preset');

-- name: update_preset_mode
UPDATE rule_modes SET title = :title, duration_s = :duration_s, do_actions = :do_actions,
    end_actions = :end_actions, suspends = :suspends
WHERE name = :name AND origin = 'preset';

-- name: get_active_mode
SELECT id, name, started_at, ends_at, actor FROM rule_mode_active WHERE id = 1;

-- name: set_active_mode
INSERT OR REPLACE INTO rule_mode_active (id, name, started_at, ends_at, actor)
VALUES (1, :name, :started_at, :ends_at, :actor);

-- name: clear_active_mode
DELETE FROM rule_mode_active WHERE id = 1;
