# Changelog

## [0.1.0] - 2026-11-02

The inventory and expense module. Stock on hand, reorder levels, categories,
locations and notes; purchases that add stock and spending together; stock
removal; a low-stock list; item editing; and purchase history and totals, stored
in the host application's main SQLite database.

## [0.1.1] - 2026-11-03

The inventory page carries the same full application menu as the dashboard.

## [0.1.2] - 2026-11-08

English/Romanian navigation and page copy, forms-engine add flows with CSRF and
input-mode support, and settings moved to the parent application.

## [0.1.3] - 2026-11-09

Pages render content through the host shell, so the host application owns the header, footer and menu. The inventory CSS moved into `templates/parts/style.html` with the content. Item saves are written to the host application log.

## [0.1.4] - 2026-11-12

The module declares the runtime functions it calls and discards results by calling directly, rather than relying on helpers the including application defines. Its smoke test signs in with a keeper ticket and sends the form token the module checks.
