function flush_para() {
  if (para != "") {
    print para
    print ""
    para = ""
  }
}
/^# Changelog$/ { next }
/^## \[/ {
  flush_para()
  print ""
  print
  print ""
  next
}
{
  if ($0 ~ /^[[:space:]]*$/) { flush_para(); next }
  if (para == "") para = $0
  else para = para " " $0
}
END { flush_para() }
