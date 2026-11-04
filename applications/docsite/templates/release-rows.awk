function esc(text) {
  gsub(/&/, "\\&amp;", text)
  gsub(/</, "\\&lt;", text)
  gsub(/>/, "\\&gt;", text)
  return text
}
function flush_para() {
  if (para != "") {
    if (note != "") note = note "<br><br>"
    note = note esc(para)
    para = ""
  }
}
function flush() {
  flush_para()
  if (version != "") {
    n++
    vers[n] = version
    dates[n] = date
    notes[n] = note
  }
  version = ""
  date = ""
  note = ""
}
/^## \[/ {
  flush()
  version = $0
  sub(/^## \[/, "", version)
  sub(/\].*/, "", version)
  date = $0
  sub(/.*\] *- */, "", date)
  next
}
{
  if (version == "") next
  if ($0 ~ /^[[:space:]]*$/) { flush_para(); next }
  if (para == "") para = $0
  else para = para " " $0
}
function vercmp(a, b,   A, B, i, x, y) {
  split(a, A, ".")
  split(b, B, ".")
  for (i = 1; i <= 3; i++) {
    x = A[i] + 0
    y = B[i] + 0
    if (x != y) return x - y
  }
  return 0
}
END {
  flush()
  for (i = 1; i <= n; i++) {
    for (j = i + 1; j <= n; j++) {
      if (vercmp(vers[i], vers[j]) < 0) {
        t = vers[i]; vers[i] = vers[j]; vers[j] = t
        t = dates[i]; dates[i] = dates[j]; dates[j] = t
        t = notes[i]; notes[i] = notes[j]; notes[j] = t
      }
    }
  }
  for (i = 1; i <= 5 && i <= n; i++) {
    printf "<div class=\"release\"><span class=\"version\">%s</span><span class=\"date\">%s</span><p class=\"note\">%s</p></div>\n", vers[i], dates[i], notes[i]
  }
}
