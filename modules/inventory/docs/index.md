# Inventory & expenses

A reusable module for what is on the shelf and what it cost. It is a
Rho module with backend, pages and SQLite storage, listed in
`modules/registry.yml`. It has no port of its own: a host application includes it
and the module registers its routes under `/expenses` on the host's router. The
aquarium application is the first host.

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

## Storage

The module does not own its records; the application that consumes it does. The
database lives under the consuming application's workspace:

```
$ROBOHUB_APP_WORKSPACE/modules/inventory/inventory.db
```

The host application owns both the workspace and the module's settings, so two
applications using the same module cannot overwrite each other's data and can
give it different values. The settings are the `config:` map on the module's
entry in the host application's `module.yml`:

```yaml
app_modules:
  - name: inventory
    route: /expenses
    config:
      currency: RON
```

`currency` is the first setting the module reads. An application that includes
the module sets `ROBOHUB_APP_MANIFEST` to its own manifest, which is how the
module finds those settings; the keeper does this when it starts a hosted
application.

## SQL

`db/schema.sql` and `db/queries.sql` are the module's own schema. The host
application declares the engine and points its `sql:` block at those files, and
generates the statement layer the included module uses. The host opens the
database and the module applies its schema on each request.

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
