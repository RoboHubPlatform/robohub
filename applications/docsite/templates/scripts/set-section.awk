# set-section.awk — rewrite a module manifest's `docs:` block for the site.
#
# The site decides where a module's pages appear, and they are always read from
# the docs/ folder the assembler filled. So the block keeps what the module says
# about itself (its title, its order) and loses where it said its pages were:
# `section`, `index` and `sources` are replaced by the site's section and
# docs/index.md. A manifest without a `docs:` block is given one.
#
# With -v name=<name>, the module is renamed in the copy: two parts of the
# ecosystem may share a name (a contract and the repository that implements it),
# and the site needs one page each.
#
# usage: awk -v section=<section> [-v name=<name>] -f set-section.awk module.yml > out.yml

function close_block() {
    if (in_docs) {
        print "  section: " section
        print "  index: docs/index.md"
        in_docs = 0
    }
}

BEGIN { in_docs = 0; seen = 0; skip_list = 0; renamed = 0 }

{
    if (name != "" && !renamed && $0 ~ /^  name:/) {
        print "  name: " name
        renamed = 1
        next
    }
    if ($0 ~ /^[^ \t#]/) {
        # A key at the top level ends whatever block was open.
        close_block()
        skip_list = 0
        if ($0 ~ /^docs:[ \t]*$/) {
            in_docs = 1
            seen = 1
            print
            next
        }
        print
        next
    }
    if (in_docs) {
        if ($0 ~ /^  [a-z_]+:/) {
            skip_list = 0
            if ($0 ~ /^  (section|index):/) { next }
            if ($0 ~ /^  sources:/) { skip_list = 1; next }
            print
            next
        }
        if (skip_list && $0 ~ /^    /) { next }
        if (skip_list && $0 ~ /^[ \t]*$/) { next }
        print
        next
    }
    print
}

END {
    close_block()
    if (!seen) {
        print ""
        print "docs:"
        print "  section: " section
        print "  index: docs/index.md"
    }
}
