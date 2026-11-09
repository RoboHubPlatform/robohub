-- name: insert_source
INSERT INTO energy_sources (name, kind, bus, address, mesh_source, rated_w, protocol)
VALUES (:name, :kind, :bus, :address, :mesh_source, :rated_w, :protocol);

-- name: list_sources
SELECT id, name, kind, bus, address, mesh_source, rated_w, power_w, voltage_mv,
       current_ma, temperature_mc, status, protocol, updated_epoch
FROM energy_sources ORDER BY kind, name;

-- name: find_source_by_name
SELECT id, name, kind, bus, address, mesh_source, rated_w, power_w, voltage_mv,
       current_ma, temperature_mc, status, protocol, updated_epoch
FROM energy_sources WHERE name = :name LIMIT 1;

-- name: update_source_reading
UPDATE energy_sources
SET power_w = :power_w, voltage_mv = :voltage_mv, current_ma = :current_ma,
    temperature_mc = :temperature_mc, status = :status,
    updated_epoch = :updated_epoch
WHERE id = :id;

-- name: delete_source
DELETE FROM energy_sources WHERE id = :id;

-- name: insert_battery
INSERT INTO energy_batteries (name, chemistry, capacity_wh, can_profile, bms_host, mesh_source)
VALUES (:name, :chemistry, :capacity_wh, :can_profile, :bms_host, :mesh_source);

-- name: list_batteries
SELECT id, name, chemistry, capacity_wh, soc_milli, soh_milli, voltage_mv,
       current_ma, temperature_mc, cell_min_mv, cell_max_mv, charge_limit_ma,
       discharge_limit_ma, can_profile, bms_host, mesh_source, status,
       updated_epoch
FROM energy_batteries ORDER BY name;

-- name: find_battery_by_name
SELECT id, name, chemistry, capacity_wh, soc_milli, soh_milli, voltage_mv,
       current_ma, temperature_mc, cell_min_mv, cell_max_mv, charge_limit_ma,
       discharge_limit_ma, can_profile, bms_host, mesh_source, status,
       updated_epoch
FROM energy_batteries WHERE name = :name LIMIT 1;

-- name: update_battery_reading
UPDATE energy_batteries
SET soc_milli = :soc_milli, soh_milli = :soh_milli, voltage_mv = :voltage_mv,
    current_ma = :current_ma, temperature_mc = :temperature_mc,
    cell_min_mv = :cell_min_mv, cell_max_mv = :cell_max_mv, status = :status,
    updated_epoch = :updated_epoch
WHERE id = :id;

-- name: delete_battery
DELETE FROM energy_batteries WHERE id = :id;

-- name: insert_grid
INSERT INTO energy_grids (name, utility, mesh_source, phases, import_limit_w,
                          export_limit_w, zero_export)
VALUES (:name, :utility, :mesh_source, :phases, :import_limit_w,
        :export_limit_w, :zero_export);

-- name: list_grids
SELECT id, name, utility, mesh_source, phases, voltage_mv, frequency_mhz,
       import_w, export_w, import_limit_w, export_limit_w, zero_export,
       synchronized, status, updated_epoch
FROM energy_grids ORDER BY name;

-- name: find_grid_by_name
SELECT id, name, utility, mesh_source, phases, voltage_mv, frequency_mhz,
       import_w, export_w, import_limit_w, export_limit_w, zero_export,
       synchronized, status, updated_epoch
FROM energy_grids WHERE name = :name LIMIT 1;

-- name: update_grid_reading
UPDATE energy_grids
SET voltage_mv = :voltage_mv, frequency_mhz = :frequency_mhz,
    import_w = :import_w, export_w = :export_w,
    synchronized = :synchronized, status = :status,
    updated_epoch = :updated_epoch
WHERE id = :id;

-- name: update_grid_zero_export
UPDATE energy_grids SET zero_export = :zero_export WHERE id = :id;

-- name: delete_grid
DELETE FROM energy_grids WHERE id = :id;

-- name: insert_load
INSERT INTO energy_loads (name, zone, priority, power_w, critical)
VALUES (:name, :zone, :priority, :power_w, :critical);

-- name: list_loads
SELECT id, name, zone, priority, power_w, critical, shed, state, updated_epoch
FROM energy_loads ORDER BY priority, name;

-- name: find_load_by_name
SELECT id, name, zone, priority, power_w, critical, shed, state, updated_epoch
FROM energy_loads WHERE name = :name LIMIT 1;

-- name: update_load_state
UPDATE energy_loads
SET state = :state, shed = :shed, updated_epoch = :updated_epoch
WHERE id = :id;

-- name: update_load_reading
UPDATE energy_loads
SET power_w = :power_w, state = :state, updated_epoch = :updated_epoch
WHERE id = :id;

-- name: set_load_shed
UPDATE energy_loads SET shed = :shed, updated_epoch = :updated_epoch
WHERE critical = 0 AND priority >= :priority;

-- name: delete_load
DELETE FROM energy_loads WHERE id = :id;

-- name: get_config
SELECT id, mode, grid_forming, zero_export, peak_shaving, tariff_optimization,
       reserve_soc_milli, load_shed_soc_milli, generator_start_soc_milli,
       generator_stop_soc_milli, charge_limit_ma, discharge_limit_ma,
       charge_voltage_mv, discharge_cutoff_mv, export_limit_w,
       solar_temp_limit_mc, battery_temp_limit_mc, source_over_voltage_mv,
       source_over_current_ma, battery_cell_delta_mv, grid_min_voltage_mv,
       grid_max_voltage_mv, grid_min_frequency_mhz, grid_max_frequency_mhz,
       generator, load_shed, tariff_peak, sim_fault, sim_tick,
       energy_today_wh, energy_total_wh, updated_epoch
FROM energy_config WHERE id = 1;

-- name: update_config_policy
UPDATE energy_config
SET mode = :mode, grid_forming = :grid_forming, zero_export = :zero_export,
    peak_shaving = :peak_shaving,
    tariff_optimization = :tariff_optimization,
    reserve_soc_milli = :reserve_soc_milli,
    load_shed_soc_milli = :load_shed_soc_milli,
    generator_start_soc_milli = :generator_start_soc_milli,
    generator_stop_soc_milli = :generator_stop_soc_milli,
    export_limit_w = :export_limit_w, updated_epoch = :updated_epoch
WHERE id = 1;

-- name: update_config_limits
UPDATE energy_config
SET charge_limit_ma = :charge_limit_ma,
    discharge_limit_ma = :discharge_limit_ma,
    charge_voltage_mv = :charge_voltage_mv,
    discharge_cutoff_mv = :discharge_cutoff_mv,
    solar_temp_limit_mc = :solar_temp_limit_mc,
    battery_temp_limit_mc = :battery_temp_limit_mc,
    source_over_voltage_mv = :source_over_voltage_mv,
    source_over_current_ma = :source_over_current_ma,
    battery_cell_delta_mv = :battery_cell_delta_mv,
    grid_min_voltage_mv = :grid_min_voltage_mv,
    grid_max_voltage_mv = :grid_max_voltage_mv,
    grid_min_frequency_mhz = :grid_min_frequency_mhz,
    grid_max_frequency_mhz = :grid_max_frequency_mhz,
    updated_epoch = :updated_epoch
WHERE id = 1;

-- name: set_config_mode
UPDATE energy_config
SET mode = :mode, grid_forming = :grid_forming, zero_export = :zero_export,
    updated_epoch = :updated_epoch
WHERE id = 1;

-- name: set_config_generator
UPDATE energy_config SET generator = :generator, updated_epoch = :updated_epoch
WHERE id = 1;

-- name: set_config_shed
UPDATE energy_config SET load_shed = :load_shed, updated_epoch = :updated_epoch
WHERE id = 1;

-- name: set_config_tariff
UPDATE energy_config
SET tariff_peak = :tariff_peak, updated_epoch = :updated_epoch
WHERE id = 1;

-- name: set_sim_fault
UPDATE energy_config SET sim_fault = :sim_fault, updated_epoch = :updated_epoch
WHERE id = 1;

-- name: set_sim_counters
UPDATE energy_config
SET sim_tick = :sim_tick, energy_today_wh = :energy_today_wh,
    energy_total_wh = :energy_total_wh, updated_epoch = :updated_epoch
WHERE id = 1;

-- name: get_fault_state
SELECT code, active, severity, message, updated_epoch
FROM energy_fault_state WHERE code = :code LIMIT 1;

-- name: set_fault_state
INSERT INTO energy_fault_state (code, active, severity, message, updated_epoch)
VALUES (:code, :active, :severity, :message, :updated_epoch)
ON CONFLICT(code) DO UPDATE SET
    active = excluded.active,
    severity = excluded.severity,
    message = excluded.message,
    updated_epoch = excluded.updated_epoch;

-- name: list_active_fault_states
SELECT code, active, severity, message, updated_epoch
FROM energy_fault_state WHERE active = 1
ORDER BY updated_epoch DESC, code;

-- name: insert_event
INSERT INTO energy_events (severity, kind, message, created_epoch)
VALUES (:severity, :kind, :message, :created_epoch);

-- name: list_events
SELECT id, severity, kind, message, created_epoch
FROM energy_events ORDER BY created_epoch DESC, id DESC LIMIT 200;

-- name: get_source
SELECT id, name, kind, bus, address, mesh_source, rated_w, power_w, voltage_mv,
       current_ma, temperature_mc, status, protocol, updated_epoch
FROM energy_sources WHERE id = :id LIMIT 1;

-- name: get_battery
SELECT id, name, chemistry, capacity_wh, soc_milli, soh_milli, voltage_mv,
       current_ma, temperature_mc, cell_min_mv, cell_max_mv, charge_limit_ma,
       discharge_limit_ma, can_profile, bms_host, mesh_source, status,
       updated_epoch
FROM energy_batteries WHERE id = :id LIMIT 1;

-- name: get_grid
SELECT id, name, utility, mesh_source, phases, voltage_mv, frequency_mhz,
       import_w, export_w, import_limit_w, export_limit_w, zero_export,
       synchronized, status, updated_epoch
FROM energy_grids WHERE id = :id LIMIT 1;

-- name: get_load
SELECT id, name, zone, priority, power_w, critical, shed, state, updated_epoch
FROM energy_loads WHERE id = :id LIMIT 1;

-- --------------------------------------------------------------------------
-- inventory module statements (canonical: modules/inventory/db/queries.sql)
-- --------------------------------------------------------------------------

-- name: insert_category
INSERT INTO categories (name) VALUES (:name);

-- name: list_categories
SELECT id, name FROM categories ORDER BY name;

-- name: insert_item
INSERT INTO items (name, category_id, unit, quantity_milli, reorder_milli,
                   location, notes)
VALUES (:name, NULLIF(:category_id, ''), :unit, :quantity_milli,
        :reorder_milli, :location, :notes);

-- name: list_items
SELECT i.id, i.name, COALESCE(c.name, '') AS category, i.category_id, i.unit,
       i.quantity_milli, i.reorder_milli, COALESCE(i.location, '') AS location,
       COALESCE(i.notes, '') AS notes
FROM items i
LEFT JOIN categories c ON c.id = i.category_id
ORDER BY i.name;

-- name: update_item_details
UPDATE items
SET name = :name, category_id = NULLIF(:category_id, ''), unit = :unit,
    reorder_milli = :reorder_milli, location = :location, notes = :notes
WHERE id = :id;

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

-- --------------------------------------------------------------------------
-- scheduler module statements (canonical: modules/scheduler/db/queries.sql)
-- --------------------------------------------------------------------------

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

-- --------------------------------------------------------------------------
-- widgets module statements (canonical: modules/widgets/db/queries.sql)
-- --------------------------------------------------------------------------

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

-- name: list_telemetry_recent
SELECT CAST(value AS TEXT) AS value_text, received_ms
FROM telemetry_reading
WHERE project = :project AND field = :field
ORDER BY received_ms DESC LIMIT 60;

-- name: update_widget_source
UPDATE widgets SET source_kind = :source_kind, source = :source, method = :method WHERE id = :id;
