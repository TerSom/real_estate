# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment & Configuration

- Python virtual environment: `venvodoo18/` (Python 3.12)
- Configuration file: `odoo.conf` (port `8018`, DB user `odoo18`, addons: `addons,custom_addons`)

## Common Commands

### Running Odoo Server
- Start server: `./venvodoo18/bin/python odoo-bin -c odoo.conf`
- Start server with auto-reload (Python & XML): `./venvodoo18/bin/python odoo-bin -c odoo.conf --dev=reload,xml`
- Install module into database: `./venvodoo18/bin/python odoo-bin -c odoo.conf -d <dbname> -i <module_name>`
- Update module in database: `./venvodoo18/bin/python odoo-bin -c odoo.conf -d <dbname> -u <module_name>`
- Update module and stop: `./venvodoo18/bin/python odoo-bin -c odoo.conf -d <dbname> -u <module_name> --stop-after-init`

### Testing
- Run all tests for module: `./venvodoo18/bin/python odoo-bin -c odoo.conf -d <dbname> --test-enable --stop-after-init -u <module_name>`
- Run tests by module tag: `./venvodoo18/bin/python odoo-bin -c odoo.conf -d <dbname> --test-enable --stop-after-init --test-tags /<module_name>`
- Run specific test class or method: `./venvodoo18/bin/python odoo-bin -c odoo.conf -d <dbname> --test-enable --stop-after-init --test-tags .<test_class>:<test_method>`

### Linting
- Configured via `ruff.toml` (Python 3.10+ target):
  - Lint check: `./venvodoo18/bin/ruff check .` or `./venvodoo18/bin/ruff check custom_addons/<module_name>`
  - Lint fix: `./venvodoo18/bin/ruff check --fix .`

### Utilities & Scaffolding
- Scaffold new custom module: `./venvodoo18/bin/python odoo-bin scaffold <module_name> custom_addons/`
- Interactive Odoo shell: `./venvodoo18/bin/python odoo-bin shell -c odoo.conf -d <dbname>`

## Architecture

- **Core (`odoo/`)**: Core ERP framework, ORM engine, HTTP server, RPC layers.
- **Official Addons (`addons/`)**: Standard upstream Odoo modules.
- **Custom Addons (`custom_addons/`)**: Workspace custom modules (e.g. `car_rental`). All custom business code resides here.
- **Module Structure**:
  - `__manifest__.py`: Module metadata, dependencies (`depends`), view/data loading sequence (`data`), frontend bundles (`assets`).
  - `models/`: Python ORM models (`models.Model`), constraints, compute methods.
  - `views/`: XML action, menu, form, list, search, and kanban definitions.
  - `security/`: Model access rules (`ir.model.access.csv`) and record rules.
  - `wizard/`: Transient models (`models.TransientModel`) and their XML views.
  - `report/`: QWeb PDF reports and SQL report views.
  - `controllers/`: HTTP controllers and routing endpoints.

## Scope Rules (IMPORTANT)

- NEVER modify Odoo core or official modules. These are read-only:
  - `odoo/` (framework, ORM, HTTP server)
  - `addons/` (standard upstream modules such as `base`, `account`, `stock`, `sale`)
  - `odoo-bin`
- ALL changes go into `custom_addons/` only.
- To change the behavior of a standard model, view, report, or controller, extend it from a custom module:
  - Python: `_inherit = 'res.partner'` (or the relevant model)
  - XML views: inherited view with `<xpath>`
  - QWeb reports: template inheritance with `t-inherit`
  - Controllers: subclass the original controller and override the method
- Reading files in `odoo/` and `addons/` for reference is fine (e.g. to find the right xpath target or field name).
- If a task seems to require editing core or official files, stop and propose an inheritance-based alternative in `custom_addons/` instead.

## Odoo 18 Specific Rules (CRITICAL — Avoid Legacy Syntax)

Claude's training data contains legacy Odoo 14–16 patterns that WILL break in Odoo 18. Strictly enforce these Odoo 18 rules:

- **Views (`<list>`, NOT `<tree>`)**:
  - Always use `<list>` instead of `<tree>` in XML view definitions.
  - Use `list,form` (not `tree,form`) in `ir.actions.act_window` `view_mode`.
  - Suffix list view XML IDs with `_view_list` (e.g., `car_rental_order_view_list`).
- **No `attrs` or `states` in XML**:
  - `attrs="{...}"` and `states="..."` are completely removed in Odoo 17/18.
  - Use inline Python expressions directly on attributes: `invisible="state != 'draft'"`, `readonly="state == 'done'"`, `required="is_company"`.
  - For `<button>`, use `invisible="state != 'draft'"` instead of `states="draft"`.
  - Note: Inside `<list>` views, use `column_invisible="parent.state == 'draft'"` to hide an entire column based on parent record, or `invisible="..."` to hide cell content per row.
- **Simplified Chatter**:
  - In Odoo 18 form views, use `<chatter/>` right after `</sheet>` instead of the legacy `<div class="oe_chatter">` block (requires inheriting `mail.thread` / `mail.activity.mixin`).
- **ORM `Command` API (No Magic Tuples)**:
  - Never use magic tuples like `(0, 0, vals)`, `(4, id)`, or `(6, 0, ids)` for `One2many` / `Many2many` fields.
  - Always import and use `Command` (`from odoo import Command`): `Command.create(vals)`, `Command.update(id, vals)`, `Command.delete(id)`, `Command.unlink(id)`, `Command.link(id)`, `Command.clear()`, `Command.set(ids)`.
- **Batch `create()` Overrides**:
  - Always decorate `create` overrides with `@api.model_create_multi` and accept `vals_list` (`def create(self, vals_list):`).
- **ORM Performance & Conventions**:
  - Always define `_description` on every new `models.Model` or `models.TransientModel`.
  - All `@api.depends` compute methods and `@api.constrains` methods MUST iterate over `self` (`for record in self:`) to handle batch recordsets safely.
  - Ensure every `@api.depends` compute method assigns a value to the target field in all code branches (even `False` or `0.0`), otherwise Odoo 18 raises a compute unassigned error.
  - Never call `search()` or `browse()` inside a loop; prefetch or batch with `read_group()` / `_read_group()` or `mapped()` before looping.

## Code Style & File Naming (Odoo Official Convention)

- One file per main model group. File name matches the model name (dots → underscores).
  - Model `<model.name>` → `models/<model_name>.py`
  - Example: `library.book` → `models/library_book.py`, `car.rental.order` → `models/car_rental_order.py`
  - If a file defines multiple models tied to one main model (e.g. an order + its lines), keep them in the same file named after the main model.
  - When extending an existing model (`_inherit`), name the file after the inherited model (e.g. `res_partner.py`, `account_move.py`).
- Same pattern for views: `views/<model_name>_views.xml`
  - Example: `views/library_book_views.xml`, `views/car_rental_order_views.xml`
- Security file stays `security/ir.model.access.csv` (+ `security/<module>_security.xml` for record rules/groups if needed).
- XML record IDs: `<model_name>_<suffix>` (model name with dots → underscores).
  - Examples: `library_book_view_form`, `library_book_view_list`, `car_rental_order_action`, `<module>_menu_root`.
- Don't restructure/reformat existing files just to apply these rules — only apply to new files or code actually being modified (avoids noisy diffs).

## Checklist When Adding New Models or Views

Whenever creating a new model or XML file, always verify all four places before finishing:
1. Import the Python file in `models/__init__.py` (or `controllers/__init__.py` / `wizard/__init__.py`).
2. Add access rights for every new `models.Model` or `models.TransientModel` in `security/ir.model.access.csv`.
3. Register new XML/CSV files in `__manifest__.py` under `'data'` in strict loading order:
   - `security/*_security.xml` (groups & record rules)
   - `security/ir.model.access.csv`
   - `data/*.xml` (sequences, cron jobs, default records)
   - `wizard/*_views.xml`
   - `views/*_views.xml`
   - `report/*_templates.xml` and `report/*_reports.xml`
   - `views/*_menus.xml` (if separated)
4. If adding JS/CSS/OWL components in `static/src/`, register them in `__manifest__.py` under `'assets': {'web.assets_backend': [...]}`.

## Git Commit Conventions

- Do NOT add `Co-Authored-By: Claude` trailer or "Generated with Claude Code" footer to commit messages.
- Commit messages should be authored as if written by Terry directly — no AI attribution.
- Follow Odoo's official commit message structure: `[TAG] <module>: short description`
- Tags (pick the one that matches the change):
  - `[FIX]` bug fix
  - `[ADD]` adding new module/feature
  - `[IMP]` incremental improvement (most common during dev)
  - `[REF]` heavy refactor/rewrite
  - `[REM]` removing dead code, views, or files
  - `[MOV]` moving files (use `git mv`, keep content unchanged)
  - `[REV]` reverting a previous commit
- Keep the short description imperative and under 50 chars, e.g.:
  - `[ADD] car_rental: scaffold vehicle and rental order models`
  - `[FIX] car_rental: correct xpath for invoice button`
  - `[IMP] car_rental: add availability check on rental confirm`
- For non-trivial changes, add a body explaining WHY the change was made, not just WHAT changed.