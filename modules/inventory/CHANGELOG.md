# Changelog

## [0.1.0] - 2026-11-02

The inventory and expense module. Stock on hand, reorder levels, categories,
locations and notes; purchases that add stock and spending together; stock
removal; a low-stock list; item editing; and purchase history and totals, stored
in the host application's main SQLite database.

## [0.1.1] - 2026-11-03

The inventory page carries the same full application menu as the dashboard.

## [0.1.2] - 2026-11-08

English/Romanian navigation and page copy, forms-engine add flows with CSRF and
input-mode support, and settings moved to the parent application.

## [0.1.3] - 2026-11-09

Pages render content through the host shell, so the host application owns the header, footer and menu. The inventory CSS moved into `templates/parts/style.html` with the content. Item saves are written to the host application log.

## [0.1.4] - 2026-11-12

The module declares the runtime functions it calls and discards results by calling directly, rather than relying on helpers the including application defines. Its smoke test signs in with a keeper ticket and sends the form token the module checks.

## [0.2.0] - 2026-11-13

Inventory is where every item of an installation lives, equipment included.
An item has a kind (consumable, part, equipment) and a handle that the rest of an
application names it by. Categories carry a kind, the capabilities an equipment
item in them can be bound to (`switch, power?`) and the category they use, and an
application seeds them from its presets (`inventory_presets`). An equipment item's
Automation tab binds each capability to a gateway source; a source is controlled
by one item at most. `inventory_resolve`, `inventory_read`, `inventory_switch`,
`inventory_consume`, `inventory_use` and `inventory_runtime_tick` are what
applications and other modules call. The gateway is the interface only: an
application that binds none has the inventory it had.

The module's tables and statements are its own, declared in its `sql:` block and
generated into each application by rho-sql 0.2; older databases get the new
columns from `ALTER TABLE` statements. The smoke test runs in the aquarium's own
repository and covers the migration, handles and bindings. `inventory_assign_handle`, `inventory_add_equipment` and `inventory_bind` let an
application fill the roles its rules name (`heater`, `light`) from a page of its own.
An item that is not bound is no longer warned about on every switch attempt; the
rule that asked says so.

## [0.2.1] - 2026-11-13

The page's message (`?msg=`) is written into its toast as a JavaScript string, so a crafted link can no longer run script on the inventory page.

## [0.2.2] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once. Today's date likewise (`rho_local_date`).
