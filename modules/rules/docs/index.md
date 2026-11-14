# Rules & modes

When something holds, do something. The engine, its tables, its page and its
evaluation are this module's; the rules are the application's — seeded from its
`presets/rules.yml`, changed by its people, kept in its database, and seen by no
other application.

## How an application uses it

Include the module after `inventory` and `journal`, and add it to `deps`. It
brings `i18n`, `inventory`, `journal`, `notifications`, `forms` and the
`robohub.alert` interface — the interface only. An application that binds
`robohub.alert` to providers in its `bind:` block gets a rule's alerts on those
channels (see {ref}`robohub-alert/index`); one that binds none gets them in the
journal.

The application:

- defines `host_shell(req, title, body, scripts)`, which draws the rules page in
  its layout;
- defines `rules_host_value(ref: string) string` — its own values that a
  condition may name (`aquarium.nitrate`), and `""` for any it does not know;
- seeds its rules and modes at startup with `rules_presets(text)`;
- calls `rules_tick()` from its background work: every few seconds, and when a
  reading arrives;
- reads the mode in force with `rules_mode()`; `appshell` shows it in the top
  bar, and its quick-mode button posts to `/rules/mode`.

## Conditions

A small fixed grammar, combined with `and`, `or`, `not` and brackets:

| Written | Reads |
|---|---|
| `heater.temperature < 24.5` | an inventory item's capability, by handle, through the gateway |
| `filter-main.switch == on` | `on`/`true` are 1, `off`/`false` 0 |
| `aquarium.nitrate >= 25` | a value the host answers (`rules_host_value`) |
| `mode == feeding` | the mode in force (`!=` too) |
| `time between 10:00 and 20:00` | the machine's clock; a window may cross midnight |

Numbers compare as numbers, in thousandths; anything else compares as text, for
`==` and `!=` only. A reading that is not there makes the condition false and is
shown on the rule: a rule never acts on a value it could not read. `and` and `or`
stop at the side that decides, so a missing reading there does not matter.

## Actions

Separated by `;`:

| Written | Does |
|---|---|
| `switch heater on` | switches an inventory item through the gateway |
| `use feeder` | one use of an item (a feeder's portion of food) |
| `alert warning "the filter draws no power"` | the journal, and every alert channel the application binds |
| `journal info "lights on"` | the journal only |
| `mode feeding`, `mode end` | starts a mode, or ends the one in force |

## A rule's states

`idle` → `pending` (the condition holds and `for` is set) → `active` (it held for
the whole wait; the `do` actions run). An active rule returns to `idle` when its
`clear` condition holds — or, with none, when the condition stops holding — and
its `else` actions run. A rule fires at most once per `cooldown`. When an action
cannot be done — an item not yet bound, a device not answering — the rule stays
where it was and tries again a minute later; the problem shows on the
rule and is written to the journal once.

## Modes

A mode is a named change for a while: starting it ends the one in force, runs its
`do` actions and suspends the rules it names; it ends after its time (or when
someone ends it) and runs its `end` actions.

## Presets

```yaml
rules:
  keep-temperature:
    when: heater.temperature < 24.5
    clear: heater.temperature > 25.5
    do: switch heater on
    else: switch heater off
  filter-stopped:
    when: filter-main.switch == on and filter-main.power < 5
    for: 60s
    cooldown: 30m
    do: alert warning "the filter draws no power"
modes:
  feeding:
    title: Feeding
    for: 10m
    do: switch filter-main off
    end: switch filter-main on
    suspends: filter-stopped
```

`rules_presets(text)` seeds them. A preset rule or mode is kept as the presets
say; one a person added is never touched; whether a rule is enabled stays the
person's choice.

## Changing a rule

Every rule has an *Edit* link on the rules page: its condition, clear
condition, wait, cooldown and actions are changed there and checked before they
are saved — a change that does not read is shown again with what was typed and
why. A preset rule that is changed becomes *edited*: the application's presets
no longer change it, and *Back to the preset* puts it back as they say it (the
presets' own values are kept in `rule_presets` each time they are applied).

## Data it keeps

In the application's database, `<workspace>/data/app.db` (or `RHO_RULES_DB`),
from the module's own `db/schema.sql`, which rho-sql generates into every
application that depends on the module:

| Table | What it holds |
|---|---|
| `rules` | Each rule: its condition, clear condition, wait, cooldown, actions, origin (`preset`, `edited`, `person`), whether it is enabled, its state and when it last fired |
| `rule_presets` | What the presets say each preset rule is, for *Back to the preset* |
| `rule_modes` | Each mode: its actions, duration, end actions and the rules it suspends |
| `rule_mode_active` | The mode in force, at most one |

The module has no settings of its own; its rules and modes are its data.

`GET /rules` is the page; `GET /api/rules` is the state of every rule and the
mode in force, as JSON.
