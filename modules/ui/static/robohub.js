/*
 * robohub.js — what every RoboHub page does in the browser, and nothing more:
 * fills links to applications (through the keeper's origin when it serves them,
 * on their own ports otherwise), shows times in the reader's zone,
 * closes an open menu when the reader clicks elsewhere, and marks the card whose
 * inspector is open. It runs again after every htmx swap.
 */
(function () {
  function fill(root) {
    root.querySelectorAll(".app-open[data-app-port]").forEach(function (el) {
      var port = el.getAttribute("data-app-port");
      var route = el.getAttribute("data-app-route") || "/";
      if (port) {
        el.href = location.protocol + "//" + location.hostname + ":" + port + route;
      }
    });
    root.querySelectorAll(".local-time[data-ms]").forEach(function (el) {
      var ms = Number(el.getAttribute("data-ms"));
      if (ms > 0) {
        el.textContent = new Date(ms).toLocaleString();
      }
    });
  }
  document.addEventListener("click", function (e) {
    document.querySelectorAll("details.rh-menu[open]").forEach(function (menu) {
      if (!menu.contains(e.target)) {
        menu.removeAttribute("open");
      }
    });
    var card = e.target.closest("[data-select]");
    if (card) {
      document.querySelectorAll("[data-select].sel").forEach(function (c) { c.classList.remove("sel"); });
      card.classList.add("sel");
    }
  });
  // A switcher in an application that is not the keeper asks the keeper which
  // applications there are. The answer is public and carries no credential.
  function tone(state) {
    if (state === "running" || state === "keeper") { return "ok"; }
    if (state === "failed") { return "bad"; }
    if (state === "starting" || state === "not-built") { return "warn"; }
    return "off";
  }
  function remote(switcher) {
    var port = switcher.getAttribute("data-keeper-port");
    var list = switcher.querySelector(".rh-apps");
    if (!port || !list || !window.fetch) { return; }
    fetch(location.protocol + "//" + location.hostname + ":" + port + "/api/v1/switcher")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.apps) { return; }
        var current = switcher.getAttribute("data-current");
        list.textContent = "";
        data.apps.forEach(function (app) {
          var a = document.createElement("a");
          a.className = "app-open" + (app.name === current ? " on" : "");
          if (app.path) {
            // Served through the keeper, on its origin: the application's own
            // port is never visited, so the keeper's cookie never reaches it.
            a.href = location.protocol + "//" + location.hostname + ":" + port + app.path;
          } else {
            a.href = "#";
            a.setAttribute("data-app-port", app.port);
            a.setAttribute("data-app-route", app.route || "/");
          }
          var label = document.createElement("span");
          var dot = document.createElement("span");
          dot.className = "rh-dot " + tone(app.state);
          label.appendChild(dot);
          label.appendChild(document.createTextNode(" " + app.title));
          var small = document.createElement("small");
          small.textContent = app.state_label || app.state;
          a.appendChild(label);
          a.appendChild(small);
          list.appendChild(a);
        });
        fill(list);
      })
      .catch(function () {});
  }
  function ready() {
    document.querySelectorAll(".rh-switch[data-keeper-port]").forEach(remote);
    fill(document);
    document.body.addEventListener("htmx:afterSettle", function () { fill(document); });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready);
  } else {
    ready();
  }
})();
