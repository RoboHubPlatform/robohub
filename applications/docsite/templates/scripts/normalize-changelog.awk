function flush_para() {
  if (para != "") {
    print para
    print ""
    para = ""
  }
}
/^# Changelog$/ { next }
# A release is a small heading under the page's "Release history", so the page's
# table of contents lists the history once rather than every version.
/^## \[/ {
  flush_para()
  print ""
  print "####" substr($0, 3)
  print ""
  next
}
{
  if ($0 ~ /^[[:space:]]*$/) { flush_para(); next }
  if (para == "") para = $0
  else para = para " " $0
}
END { flush_para() }
