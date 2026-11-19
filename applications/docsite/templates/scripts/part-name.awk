# part-name.awk — the name a part goes by in the assembled tree.
#
# `rho req` names a module nested in a repository by its `requirements: name:`
# when it has one, else by its module name; in the tree the part is a folder of
# the top level, which `rho req` names by the folder. So the folder is given that
# same name, and a qualified reference (`robohub-alert:ADR-0001`) or a parent
# resolves in the tree as it does in the repositories.
#
# It prints the part's name and then the module's own name, on one line; they
# differ for a module renamed for `rho req` (the gateway contract is the module
# robohub-gateway, a name the gateway repository has too), whose manifest is
# then renamed in the copy as well.
#
# usage: awk -f part-name.awk module.yml   (prints "<part> <module>", or nothing)

BEGIN { block = ""; module_name = ""; req_name = "" }

/^[^ \t#]/ {
    block = $0
    sub(/:.*/, "", block)
    if ($0 ~ /^requirements:[ \t]*\{/) {
        line = $0
        if (match(line, /[{,][ \t]*name:[ \t]*[^,}]+/)) {
            value = substr(line, RSTART, RLENGTH)
            sub(/^[{,][ \t]*name:[ \t]*/, "", value)
            gsub(/[ \t"']+$/, "", value)
            gsub(/^["']/, "", value)
            req_name = value
        }
    }
    next
}

/^  name:/ {
    value = $0
    sub(/^  name:[ \t]*/, "", value)
    sub(/[ \t]+#.*$/, "", value)
    gsub(/["' \t]/, "", value)
    if (block == "module" && module_name == "") { module_name = value }
    if (block == "requirements" && req_name == "") { req_name = value }
}

END {
    if (module_name == "") { exit }
    if (req_name != "") { print req_name " " module_name } else { print module_name " " module_name }
}
