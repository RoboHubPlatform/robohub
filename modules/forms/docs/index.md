# Forms

A schema-driven form engine. A module declares its form as data — a list of
fields, each naming its kind, its label, its validation rules and its default —
and this engine renders the controls, manages the submitted values, reports the
errors and hands the payload back. The same styling, the same error handling
and the same input controls serve every form in every host, so an upgrade or a
new global rule is written once.

## How an application uses it

Add `forms` to `deps` and include it. It needs no host hooks and serves no
routes. Put `forms_style()` in the layout once so the controls look the same in
every form. Every shared module with a form (`appshell`, `logging`,
`inventory`, `scheduler`, `widgets`, `rules`) depends on it, and so does each
module's settings tab.

## The idea

A form is metadata, and rendering is the engine's job. A module that wants a
form:

1. declares a fixed `FormField` array describing its fields,
2. hands it to the engine with its length to render,
3. lets the engine read the submitted body back into it,
4. asks the engine to validate (it writes a per-field error into it),
5. reads the values back out - `forms_value` or `forms_payload` - once they pass.

The fields are passed as a dynamic array `[FormField]` with a count, because
that is what both backends can index: `[]FormField` in Go, `FormField*` in C. An
enclosing `Slice[FormField]` carries its storage through a pointer that Go
cannot index.

## A field

```rho
FormField{ "meshes", "select", "Gateway project",
    "The project whose gateway and devices this application uses.",
    "Choose a gateway project", false, "", "alpha|Alpha,beta|Beta", "alpha", "", "" }
```

The fields, in order:

| name | kind | label | hint | placeholder | required | pattern | options | value | err | input_mode |
|------|------|-------|------|-------------|----------|---------|---------|-------|-----|------------|
| the key | how it is drawn | what the user reads | help under it | ghost text / select prompt | must be filled | the rule | `value\|label,value\|label` for a select | the submitted answer | the last validation message | a mobile keyboard hint |

`kind` is `text`, `password`, `number`, `select`, `textarea`, `toggle` or
`hidden`. `pattern` is one of `ip`, `number`, `host`, `email`, `url`, `plain`,
or empty for none. `input_mode` gives a text field a mobile keyboard hint such as
`decimal` or `numeric`, or is empty.

`forms_open` takes the active locale as its last argument and translates the
default submit label; a caller may pass `i18n_t(req, "common.save")` instead.

## The round trip

```rho
// A consumer's own schema, drawn from its own defaults.
fn my_schema(fields: [FormField]) void {
    fields[0] = FormField{ "gateway", "text", "Gateway URL", "", "",
        true, "host", "", my_default("gateway"), "", "" }
    fields[1] = FormField{ "token", "password", "Token", "", "",
        false, "", "", my_default("token"), "", "" }
}

fn my_page(req: Request) Response {
    var schema: FormField[2]
    my_schema(schema)
    let content: string = forms_open(schema, 2, "/configure", "", i18n_locale(req))
    return html(status_ok(), "<h1>Configure</h1>" + content)
}

fn my_save(req: Request) Response {
    var schema: FormField[2]
    my_schema(schema)
    let body: string = request_body(req)
    // A submit has to carry the token the page drew; a cross-site form cannot.
    if !forms_csrf_ok(body) {
        return html(status_ok(), "<h1>Configure</h1><p>Refused: no form token.</p>")
    }
    forms_read(schema, 2, body)
    if !forms_validate(schema, 2) {
        let content: string = forms_open(schema, 2, "/configure", "", i18n_locale(req))
        return html(status_ok(), "<h1>Configure</h1>" + content)
    }
    // Valid: use what the user typed.
    my_persist("gateway", forms_value(schema, 2, "gateway"))
    my_persist("token", forms_value(schema, 2, "token"))
    return redirect("/configure")
}
```

The engine writes the submitted value and the error into the caller's own
array, so after a failed submit the same array re-renders with the user's input
and the highlights in place. Nothing here knows what the data means; it only
collects valid state and hands it across.

## CSRF

Every form `forms_open` draws embeds the application's token in a hidden `csrf`
input; a form drawn by hand adds it with `forms_csrf_field()`. A consumer
verifies a submit with `forms_csrf_ok(body)` before acting on it; a cross-site
request cannot read that token from the victim's own page, so it cannot echo it,
and the forged post is refused.

The token is 256 random bits, made on first use and kept owner-only in the
application's workspace (`<workspace>/data/csrf.txt`). When no random value can
be had, the token is empty and every submit is refused rather than accepting a
guessable one. A token written by an older release is replaced.
