#!/bin/sh
# module-reference.sh — the reference table of a shared module, as Markdown.
#
# Read from what the module itself declares, so it cannot drift from the code:
# the names it exports (provides.exports in module.yml), the routes it
# registers on the host's router (`route` lines in its sources), and the host
# hooks it calls — functions named host_* (or <module>_host_*) that the application including the
# module has to define, because the module calls them and does not.
#
# usage: module-reference.sh <module-dir>   (prints to standard output)

dir="$1"
manifest="$dir/module.yml"
[ -f "$manifest" ] || exit 0

import=$(awk '/^provides:/{p=1;next} /^[^ #]/{p=0} p && /^  import:/{print $2; exit}' "$manifest")
exports=$(awk '/^provides:/{p=1;next} /^[^ #]/{p=0} p && /^  exports:/{e=1;next} p && e && /^    - /{print $2; next} p && e && /^  [a-z]/{e=0}' "$manifest")
routes=$(grep -h '^route ' "$dir"/src/*.rho 2>/dev/null | awk '{m=$2; p=$3; h=$5; gsub(/"/,"",p); print m " " p " " h}')
called=$(grep -hoE '\b([a-z]+_)?host_[a-z_]*\(' "$dir"/src/*.rho 2>/dev/null | tr -d '(' | sort -u)
defined=$(grep -hoE '^fn ([a-z]+_)?host_[a-z_]*\(' "$dir"/src/*.rho 2>/dev/null | sed 's/^fn //; s/($//' | sort -u)

printf '\n\n## Reference\n\n'
printf 'Generated from the module'"'"'s manifest and sources when this site was built.\n\n'
if [ -n "$exports" ]; then
    if [ -n "$import" ]; then
        printf '**Exports** — what an application may call (`provides.exports`, imported as `%s`):\n\n' "$import"
    else
        printf '**Exports** — what an application may call (`provides.exports`):\n\n'
    fi
    for name in $exports; do printf -- '- `%s`\n' "$name"; done
    printf '\n'
fi
if [ -n "$routes" ]; then
    printf '**Routes** — registered on the host application'"'"'s router:\n\n'
    printf '| Method | Path | Handler |\n|---|---|---|\n'
    printf '%s\n' "$routes" | while read -r method path handler; do
        printf '| %s | `%s` | `%s` |\n' "$method" "$path" "$handler"
    done
    printf '\n'
fi
hooks=""
for name in $called; do
    case " $(echo $defined) " in
        *" $name "*) ;;
        *) hooks="$hooks $name" ;;
    esac
done
if [ -n "$hooks" ]; then
    printf '**Host hooks** — functions the application must define, because this module calls them:\n\n'
    for name in $hooks; do printf -- '- `%s`\n' "$name"; done
    printf '\n'
fi
