# Inventory & expenses

What is on the shelf, what is installed, and what it cost — and, when the
application binds a gateway, which device each piece of equipment is. The module
has pages, a backend and SQL tables; it has no port of its own. A host
application includes it and the module registers its pages on the host's router
(`/expenses`, `/devices`). Aquarium and energy include it.

## How an application uses it

Include the module and add it to `deps`. It brings `i18n`, `settings`,
`notifications`, `forms` and the `robohub.gateway` interface — the interface
only, never a provider. An application that binds a gateway (see
{ref}`robohub-gateway-contract/index`) can connect equipment to devices; one that
binds none still has an inventory.

The application:

- defines `host_shell(req, title, body, scripts)`: the module's pages render
  content only, so the header, footer and menu are always the application's. The
  inventory's CSS travels with the content;
- seeds its categories at startup with `inventory_presets(text)` (below);
- calls `inventory_runtime_tick()` from its background work, if it wants switch
  runtime counted;
- defines the `host_devices_*` hooks for the Devices page (below);
- adds the module's settings tab: `inventory_settings_form` and
  `inventory_settings_save`, combined through `host_settings_tabs/form/save` (see
  {ref}`appshell/index`).

## What it records

An **item** has a name, a category, a unit, a quantity on hand, a reorder level,
a location and notes. The inventory page shows what is on hand and marks an item
that has reached its reorder level.

A **purchase** has an item, a category, a quantity, a unit price, a store, a
date and a comment. Recording one adds the spending and increases the item's
stock. Money is integer cents and quantity is thousandths, so a total does not
depend on floating-point spelling.

Stock also leaves the shelf through **Remove from stock**, which records a
negative movement. An item can be edited without losing its quantity or its
purchase history.

## Kinds, handles and categories

Everything an installation has is an item, of one of three **kinds**:
*consumable* (used up: food, fertiliser, test reagents), *part* (fitted and
replaced: filter media, fuses) and *equipment* (installed: the filter, the
heater, the light). An item's **handle** — `filter-main` — is the name every
other part of the application uses for it.

The categories are the application's. It seeds them from the text of its
`presets/inventory.yml` by calling `inventory_presets(text)`:

```yaml
categories:
  food:
    name: Food
    kind: consumable
  filters:
    name: Filters
    kind: equipment
    capabilities: switch, power?
  feeders:
    name: Feeders
    kind: equipment
    capabilities: press
    uses: Food
```

A category's `capabilities` are what an equipment item in it can be bound to; a
trailing `?` marks one that may stay unbound. `uses` names the category one use
of the item consumes from. A preset category keeps its name; a category a person
adds may be renamed or deleted.

## Automation

When the application binds a gateway, an equipment item has an **Automation**
tab: one row per capability of its category, each bound to a gateway source
chosen from the sources reporting that signal. A capability the item drives (a
switch) is bound for control, one it only reports (power, temperature) for
reading; a source is controlled by one item at most, so two items cannot fight
over one relay.

Rules, dashboard cards and chores name `handle.capability`, never a device.
Replacing a plug is one binding changed; nothing that names the item changes.
What the application and other modules call:

| Function | What it does |
|---|---|
| `inventory_resolve(handle, capability)` | The gateway source bound to it, or `""` |
| `inventory_read(handle, capability)` | Its newest reading |
| `inventory_switch(handle, on, actor)` | Switches it through the gateway, and logs who asked |
| `inventory_consume(handle, quantity_milli, reason, for_ref)`, `inventory_return(...)` | Takes stock off, or puts it back, with a movement saying why |
| `inventory_use(handle, actor)` | One use of an item that uses a category (a feeder's portion) |
| `inventory_runtime_tick()`, `inventory_runtime_seconds(handle)` | Counts switch runtime from the gateway's history; the runtime counted so far |
| `inventory_choices(category, kind)`, `inventory_item_name(handle)`, `inventory_item_id(handle)` | Items as choices for a form; one item's name; its id |
| `inventory_automated()` | Whether a gateway is bound |

## The Devices page

`/devices` is where an application says what is behind each piece of equipment
its rules name: which item, and which gateway source each of its capabilities
reads. It is one page for every application, in sections the application names,
and a section shows either or both of:

- **roles** — a handle the rules use (`heater`), filled by one item at a time:
  any equipment, or a new item made for it. Choosing another item moves the
  handle to it;
- **items** — every equipment item of the section's categories, with a form to
  add another to one of them.

What differs between applications is asked of the application:

| Hook | Answers |
|---|---|
| `host_devices_sections(req)` | One section per line, `key\|label`; an empty label shows no heading |
| `host_devices_roles(req, key)` | The section's roles, one per line: `handle\|label\|category\|capabilities\|hint` |
| `host_devices_categories(req, key)` | The categories the section lists and adds to, comma-separated, or `""` |
| `host_devices_query(req)` | What the page keeps in its address across a save (`tank=2`), or `""` |
| `host_devices_intro(req)` | What is shown above the sections (a tank chooser), or `""` |
| `host_devices_value(capability, text)` | A reading as the page shows it (`1.2 kW`) |
| `host_devices_added(id, category)` | What follows an item added on the page |
| `host_devices_changed(handle, what)` | A mapping changed; the application's journal is the usual place |

The aquarium has one unnamed section of roles, one tank at a time; energy has a
section per group (generation, storage, grid, loads) listing its equipment. An
item is only ever added to a category its section offers.

## Settings

Kept in the application's settings store (see {ref}`settings/index`) and shown
on the module's settings tab:

| Key | Default | What it is |
|---|---|---|
| `inventory.currency` | `RON` | The currency prices are shown in (`RON`, `EUR`, `USD`) |
| `inventory.default_unit` | — | The unit a new item starts with |
| `inventory.reorder` | `0` | The reorder level a new item starts with |

An application from before the settings store kept these as a `config:` map on
the module's entry under `app_modules:` in its manifest (`ROBOHUB_APP_MANIFEST`);
that map is still read when the store has no value.

## Data it keeps

The records belong to the application that includes the module, not to the
module: they are in the application's database, `<workspace>/data/app.db` (or
`RHO_INVENTORY_DB`), so two applications using the module never share data.

| Table | What it holds |
|---|---|
| `categories` | The categories, their kind, capabilities and what they use; whether a preset or a person made each |
| `items` | What is on hand: kind, handle, quantity, reorder level, location, switch runtime, a use's portion |
| `item_bindings` | Which gateway source each equipment capability is bound to, and whether for control or reading |
| `expenses` | One purchase line each, in cents and thousandths |
| `stock_movements` | Every change to the stock, signed, with why |

`db/schema.sql` and `db/queries.sql` are the module's own, declared in its
`sql:` block. rho-sql generates them into every application that depends on the
module, before the application's own statements, so an application does not
repeat them. A column added in a later version is both in its table's `CREATE`
and in an `ALTER TABLE ... ADD COLUMN` after it, so a new database and an older
one end with the same table.

Item saves, deletions, bindings and switches are written to the application log
under the `inventory` subject.
