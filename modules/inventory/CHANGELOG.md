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

## [0.2.3] - 2026-11-13

A purchase's total is reckoned in 64 bits (100 units at 500.00 overflowed); a stock taken below zero is shown negative instead of as four billion; a decimal comma (2,50) is a decimal point; a capability bound from the Automation tab is kept under its name (`power`, not `power?`), so it is found again.

## [0.2.4] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. The unprefixed `trim`, `url_decode` and `form_value` this module leaked into every application are gone; a `%` not followed by two hex digits is kept as written instead of becoming a zero byte.

## [0.3.0] - 2026-11-14

The Devices page is the inventory's: `/devices`, one page for every application, where what is behind each piece of equipment is chosen — which item fills a role the rules name, and which gateway source each capability reads — and equipment is added to a section's categories. The aquarium and energy each had their own; what differs between them is asked of the application through `host_devices_*` functions, which an application that includes the inventory now defines (see Devices in the docs). An item is only added to a category its section offers.

## [0.3.1] - 2026-11-14

One item is looked up, not found in a list of every item: `inventory_resolve` — what every reading and switch of a rule goes through — reads the item by handle or id and its one binding, where it read up to 512 items and 512 bindings each time; `inventory_item_id`, `inventory_item_name`, `inventory_consume` and `inventory_runtime_seconds` likewise. Its route handlers, helpers and constants carry the module's prefix; unprefixed, they were in the namespace of every application that includes the module. (`items_add` is `inventory_items_add`, `unquote` is `inventory_unquote`, `ITEM_CAPACITY` is `INVENTORY_ITEM_CAPACITY`, and so on.)

## [0.3.2] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. Copies of helpers the toolchain now provides (`i64_to_str`, `str_lower`, `str_field`, `json_str_field`, `escape_html`) are gone. It declares the i18n module it uses. Needs rho 0.8.0.

## [0.3.3] - 2026-11-14

An item can be deleted from its edit page (its bindings and stock history go with it; its purchases stay in the expenses), and a category a person added can be renamed, or deleted while empty — a category the application's presets keep (`origin = 'preset'`) cannot, since the application reads it by name. The item edit form carries the form token. `inventory_return` puts stock back, the opposite of `inventory_consume`.

## [0.3.4] - 2026-11-14

Its settings form is its own (`inventory_settings_form`, `inventory_settings_save`), shown by an application as one of its settings tabs.

## [0.4.0] - 2026-11-14

It lists what other code may use (`provides.exports`, imported as `robohub.inventory`). An application that includes it still reaches everything, and a build (rho 0.8.3) names each call to a function outside the list. The list is what the applications and modules of the ecosystem call; anything else is the module's own and may change without notice.
