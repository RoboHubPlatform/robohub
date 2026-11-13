# Inventory & expenses

A reusable module for what is on the shelf and what it cost. It is a
Rho module with backend, pages and SQLite storage, listed in
`modules/registry.yml`. It has no port of its own: a host application includes it
and the module registers its routes under `/expenses` on the host's router. The
aquarium application is the first host.

## Host shell

The module registers `/expenses`, but it renders content only. Its pages call
the host's `host_shell(req, title, body, scripts)`, so the header, footer and
menu always belong to the application the module is included in. The inventory
CSS travels in `templates/parts/style.html` and is inserted with the content,
which is what keeps the tabs, summaries and low-stock badges working under any
host shell.

## What it records

An **item** has a name, a category, a unit, a quantity on hand, a reorder level,
a location and notes. The inventory table shows what is on hand and marks an
item that has reached its reorder level.

A **purchase** has an item, a category, a quantity, a unit price, a store, a date
and a comment. Recording one does two things: it adds the spending, and it
increases the item's stock. Money is integer cents and quantity is thousandths,
so a total does not depend on floating-point spelling.

Stock also leaves the shelf through **Remove from stock**, which records a
negative movement. An item's page can be edited without losing its quantity or
its purchase history.

## Kinds, handles and categories

Everything an installation has is an item, of one of three **kinds**:
*consumable* (used up: food, fertiliser, test reagents), *part* (fitted and
replaced: filter media, fuses) and *equipment* (installed: the filter, the
heater, the light). An item's **handle** — `filter-main` — is the name every
other part of the application uses for it.

The categories are the application's. It seeds them from its presets, the text
of its `presets/inventory.yml`, by calling `inventory_presets(text)`:

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
of the item consumes from.

## Automation

When the application binds a gateway (`robohub.gateway`), an equipment item has
an **Automation** tab: one row per capability of its category, each bound to a
source of the gateway, chosen from the sources reporting that signal. A source is
controlled by one item at most. An application that binds no gateway has no
Automation tab, and the module is the inventory it always was.

What the application and other modules call:

| Function | What it does |
|---|---|
| `inventory_resolve(handle, capability)` | the gateway source bound to it, or `""` |
| `inventory_read(handle, capability)` | its newest reading |
| `inventory_switch(handle, on, actor)` | switches it through the gateway, and logs who asked |
| `inventory_consume(handle, quantity_milli, reason, ref)` | takes stock off, with a movement saying why |
| `inventory_use(handle, actor)` | one use of an item that uses a category (a feeder's portion) |
| `inventory_runtime_tick()` | counts switch runtime from the gateway's history; call it from background work |
| `inventory_runtime_hours(handle)`, `inventory_runtime_seconds(handle)` | the runtime counted so far |
| `inventory_presets(text)` | seeds the categories from the application's presets |
| `inventory_choices(category, kind)`, `inventory_item_name(handle)`, `inventory_item_id(handle)` | items as choices for a form; one item's name and unit; its id |
| `inventory_assign_handle(id, handle)`, `inventory_add_equipment(name, category, handle)`, `inventory_bind(id, capability, source)` | what an application's own device page (filling its roles) calls |

Rules, dashboard cards and chores name `handle.capability`; replacing a plug is
one binding changed, and nothing that names the item changes.

## Storage

The module does not own its records; the application that consumes it does. The
database lives under the consuming application's workspace:

```
$ROBOHUB_APP_WORKSPACE/data/app.db
```

The host application owns both the workspace and the module's settings, so two
applications using the same module cannot overwrite each other's data and can
give it different values. The settings are the `config:` map on the module's
entry in the host application's `module.yml`:

```yaml
app_modules:
  - name: inventory
    route: /expenses
    version: ">=0.1.0"
    config:
      currency: RON
```

`currency` is the first setting the module reads. An application that includes
the module sets `ROBOHUB_APP_MANIFEST` to its own manifest, which is how the
module finds those settings; the keeper does this when it starts a hosted
application.

## SQL

`db/schema.sql` and `db/queries.sql` are the module's own, declared in its
`sql:` block with no driver. rho-sql (0.2) generates them into every application
that depends on the module, before the application's own statements, so an
application does not repeat them; an application that still does is told which
copies it can remove. A column added in a later version is both in its table's
`CREATE` and in an `ALTER TABLE ... ADD COLUMN` after it, so a new database and
an older one end with the same table.

## Routes

| Route | Meaning |
|-------|---------|
| `GET /` | stock, reorder list, purchases and totals |
| `GET /items/edit?id=` | edit one item |
| `POST /items/add` | add an item |
| `POST /items/edit` | save an item |
| `POST /items/consume` | remove stock from an item |
| `POST /expenses/add` | record a purchase and increase stock |
| `POST /expenses/delete` | remove a purchase without changing stock |
| `POST /categories/add` | add a category |
| `GET /items/automation?id=` | an equipment item's bindings |
| `POST /items/bind` | bind (or, with no source, unbind) one capability |
| `POST /items/switch` | switch an item on or off through the gateway |

Item saves and stock changes are written to the host application log under the `inventory` subject.
