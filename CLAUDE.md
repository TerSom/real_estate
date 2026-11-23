# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Project Context

- Target version: **Odoo 20.0 Community**. Do not apply Odoo 18 assumptions without checking compatibility.
- Repository: Odoo server source code plus custom business modules.
- Main work directory: `custom_addons/`.
- Discover available modules from `custom_addons/` and inspect the requested module before making changes.
- Support any custom Odoo 20 addon; do not assume a particular business domain or module name.
- Prefer small, focused changes. Do not refactor unrelated files.

## Environment & Configuration

- Python version: 3.12; Ruff configuration should target `py312` in `ruff.toml`.
- Virtual environment: `venvodoo20/`.
- Python executable: `./venvodoo20/bin/python`.
- Odoo configuration file: `odoo.conf`.
- Expected development HTTP port: `8020` **if configured in `odoo.conf`**.
- Expected addons path: `addons,custom_addons` (check actual `addons_path` in `odoo.conf`; built-in `odoo/addons` is also part of Odoo's loading mechanism).
- Database name and PostgreSQL user must be read from the actual configuration or task; never assume them.
- Always run commands from the repository root unless instructed otherwise.
- Confirm that `venvodoo20/`, `odoo.conf`, and the target module exist before using commands.

## Common Commands

### Running Odoo

```bash
# Start the server
./venvodoo20/bin/python odoo-bin -c odoo.conf

# Development autoreload (use only when needed)
./venvodoo20/bin/python odoo-bin -c odoo.conf --dev=reload,xml

# Install a new custom module into the selected development database
./venvodoo20/bin/python odoo-bin -c odoo.conf -d <db_name> -i <module_name> --stop-after-init

# Update an installed module on a development database
./venvodoo20/bin/python odoo-bin -c odoo.conf -d <db_name> -u <module_name> --stop-after-init

# Open the interactive Odoo shell
./venvodoo20/bin/python odoo-bin shell -c odoo.conf -d <db_name>

# Scaffold a new module (only when requested)
./venvodoo20/bin/python odoo-bin scaffold <module_name> custom_addons/
```

### Testing

```bash
# Install the module and run its tests on an expendable development DB
./venvodoo20/bin/python odoo-bin -c odoo.conf -d <db_name> -i <module_name> --test-enable --stop-after-init

# Update the module and run its tests
./venvodoo20/bin/python odoo-bin -c odoo.conf -d <db_name> -u <module_name> --test-enable --stop-after-init

# Run tagged module tests while updating the module
./venvodoo20/bin/python odoo-bin -c odoo.conf -d <db_name> -u <module_name> --test-tags /<module_name> --stop-after-init

# Run a specific test class/method when the tag exists
./venvodoo20/bin/python odoo-bin -c odoo.conf -d <db_name> -u <module_name> --test-tags .<test_class>:<test_method> --stop-after-init
```

### Linting & Static Checks

```bash
# Use Ruff from the virtualenv when installed
./venvodoo20/bin/ruff check custom_addons/

# Limit checks to the module being changed
./venvodoo20/bin/ruff check custom_addons/<module_name>/

# Optional autofix: review the diff afterward
./venvodoo20/bin/ruff check --fix custom_addons/<module_name>/

# Python syntax check
./venvodoo20/bin/python -m compileall -q custom_addons/<module_name>/

# Review modified files
git diff --check
git diff -- custom_addons/<module_name>/
```

If `./venvodoo20/bin/ruff` is not installed, use the `ruff` executable available in the environment. Do not install dependencies without approval.

### Odoo Source Upgrade Helper (Custom Code Only)

```bash
# Review the available CLI options first
./venvodoo20/bin/python odoo-bin upgrade_code --help

# Preview available source-code rewrites from 18.0 to 20.0
./venvodoo20/bin/python odoo-bin upgrade_code --from 18.0 --to 20.0 --addons-path custom_addons/ --dry-run
```

- Run a non-dry-run source rewrite only after explicit approval and on a dedicated Git branch.
- `upgrade_code` changes source code; it is **not** a database migration.
- Check the installed Odoo 20 CLI and scripts under `odoo/upgrade_code/` before using version/script arguments.

## Architecture & Codebase Structure

- `odoo/`: core runtime and framework (read-only).
  - `odoo/orm/`: models, fields, domains, queries, constraints, caching.
  - `odoo/http/`: HTTP routing and request handling.
  - `odoo/addons/`: foundational framework modules, including `base` and `web` (read-only).
  - `odoo/upgrade_code/`: Odoo-provided source-rewrite scripts (read-only).
- `addons/`: official upstream business applications such as `mail`, `sale`, `stock`, and `account` (read-only).
- `custom_addons/`: all custom feature development.

A custom addon typically contains:

- `__manifest__.py`: metadata, `depends`, `data`, and `assets`.
- `__init__.py`: Python package imports.
- `models/`: models, extensions, compute methods, and constraints.
- `views/`: model views, actions, and menus.
- `security/`: groups and Odoo 20 access records.
- `wizard/`: `models.TransientModel` workflows and views.
- `report/`: QWeb reports and report actions.
- `controllers/`: HTTP/JSON-RPC routes.
- `static/src/`: JavaScript, OWL components, CSS/SCSS, and templates.
- `tests/`: automated module tests.

## Scope Rules (Critical)

- **Never modify** `odoo/`, `odoo/addons/`, `addons/`, `odoo-bin`, or upstream framework files.
- All custom functionality must live under `custom_addons/`.
- Reading core and official addons for reference is permitted and encouraged.
- To extend standard features, use extension mechanisms:
  - Python models: `_inherit = 'res.partner'` (or the appropriate model).
  - XML views: inherited `ir.ui.view` records and accurate `<xpath>` selectors.
  - QWeb templates: Odoo-supported template inheritance (`inherit_id` or `t-inherit` as appropriate to context).
  - HTTP controllers: subclass and redecorate overridden routes where required.
  - JS/OWL: registry entries, supported services, and patches when appropriate.
- If a requirement seems to need a core edit, explain the issue and propose an addon-based solution.
- Do not restructure unrelated files or change code style project-wide.

## Odoo 20 Breaking Changes & Conventions

### 1. Security: `ir.access` (Not the Odoo 18 ACL/Record Rule Layout)

- Odoo 20 uses the `ir.access` model and typically `security/ir.access.csv`.
- Do **not** create new `ir.model.access.csv` ACLs or old `ir.rule` definitions for Odoo 20 code.
- The CSV header is **exactly**:

```csv
id,name,model_id,group_id/id,operation,domain
```

- `operation` is a permitted combination of `c` (create), `r` (read), `u` (write/update), and `d` (delete), in that order; examples: `r`, `cru`, `crud`.
- A record with a `group_id` provides a **permission** to that group; a record without `group_id` is a **restriction**. These have different combination semantics.
- For access to all records, leave `domain` empty. Use a domain only where record filtering is intended.
- Example (replace model and group with real XML IDs):

```csv
id,name,model_id,group_id/id,operation,domain
access_example_record_user,Example Record User,model_example_record,base.group_user,cru,
```

- Define custom `res.groups` in an XML file if needed, and load that file **before** `security/ir.access.csv`.
- Review permissions **and** restrictions across user roles and companies; do not use `sudo()` to bypass access errors without a clear security justification.
- Refer to `odoo/addons/base/models/ir_access.py` and `odoo/addons/base/security/ir.access.csv` when uncertain.

### 2. ORM & Python

- Use Odoo 20 ORM APIs as implemented in the local checkout; do not copy deprecated methods from older versions.
- SQL constraints must be declared with `models.Constraint(...)`; do not add `_sql_constraints` for new Odoo 20 code.
- Example:

```python
from odoo import fields, models

class ExampleRecord(models.Model):
    _name = 'example.record'
    _description = 'Example Record'

    name = fields.Char(required=True)
    amount = fields.Float(required=True)

    _check_amount = models.Constraint(
        'CHECK(amount >= 0)',
        'Amount cannot be negative.',
    )
```

- Use `models.Index` or `models.UniqueIndex` when the schema calls for indexes; confirm exact local syntax.
- Keep business validations that cannot be expressed safely in SQL in `@api.constrains` methods.
- Use `@api.model_create_multi` for `create()` overrides, accept `vals_list`, and call `super()`.
- Define `_description` for each new `models.Model` and `models.TransientModel`.
- Treat `self` as a recordset: batch compute methods and constraints should work for multiple records.
- Compute methods must assign their field on every record in all control paths.
- Use `@api.depends` with actual dependency field names and `@api.depends_context` when needed.
- Use Odoo `fields.Command` / `Command` for relational updates instead of manually writing numeric command tuples. Check the import style used in local Odoo 20 source.
- For display names, use supported `display_name` computation patterns; do not reintroduce obsolete `name_get()` overrides.
- Prefer `has_access()` / `check_access()` where relevant instead of legacy access-check APIs; inspect actual method signatures first.
- Avoid `read_group()` patterns carried over from earlier versions; inspect `_read_group()` and current aggregation APIs.
- Use `ensure_one()` only for methods that genuinely require one record.
- Use `ValidationError` for data validity issues and `UserError` for appropriate user-facing business errors.

### 3. ORM Performance

- Avoid N+1 queries and repeated `search()` / `search_count()` calls inside record loops.
- Prefer ORM prefetching, `mapped()`, `grouped()`, `_read_group()` or batch queries when appropriate.
- Keep computed fields and onchange methods lightweight; do not put side effects in compute methods unless required.
- Avoid raw SQL when the ORM can do the job; if raw SQL is needed, parameterize safely and preserve access semantics.
- Do not use `sudo()` as a generic fix for permissions or multi-company issues.
- Respect company context and relational `check_company` behavior for cross-company data.

### 4. XML Views

- Use `<list>` instead of obsolete `<tree>` for new list views.
- Use `view_mode="list,form"` rather than `tree,form`.
- Do not use old `attrs` or `states` XML attributes.
- Use direct expressions such as `invisible="state != 'draft'"` and `readonly="state == 'done'"`.
- Use `column_invisible` for whole list columns when appropriate; verify the evaluation context, especially `parent` in relational subviews.
- Use `<chatter/>` in form views when the model supports mail features (`mail.thread`, `mail.activity.mixin` as required).
- Preserve inherited view structure. Verify the target XML ID and xpath against local Odoo 20 source before editing.
- Make sure referenced fields, button methods, view modes, and domain expressions exist.
- Use XML escaping correctly (for example, `&amp;` for `&` in XML attribute values).
- Check supported icons before using them. Odoo 20 adopts Material Symbols; do not blindly convert `fa-*` names to guessed Material Symbol identifiers.

### 5. HTTP Controllers & APIs

- Prefer `@http.route(..., type='jsonrpc')` for JSON-RPC controllers; `type='json'` is a deprecated alias.
- Use `type='http'` for ordinary HTTP endpoints.
- Verify `auth`, `methods`, `csrf`, `cors`, and `website` settings against the endpoint requirements.
- Do not expose private records through `auth='public'` or `auth='none'` without explicit review.
- Validate input, enforce relevant authorization, and avoid leaking tracebacks or internal secrets in API responses.
- Follow the installed Odoo 20 router/controller APIs when overriding inherited routes.

### 6. Inventory, Accounting & Integrations

- On Odoo 20 `stock.move`, use the current `uom_id` field instead of assuming the older `product_uom` field still exists.
- Verify renamed fields and methods in `stock.move`, `stock.move.line`, `stock.picking`, and `account.move` locally before changing integrations.
- Use real Odoo stock workflows; do not directly force stock state or bypass reservations/valuations.
- Do not post invoices, confirm payments, modify inventory, or create external transactions as a side effect of code inspection.
- Keep optional integration features in separate addons when that improves modularity; declare dependencies explicitly in each manifest.

### 7. OWL, JavaScript & Assets

- Inspect the Odoo 20 web client implementation before writing OWL components, services, or patches.
- Use supported registries, components, and assets; avoid unsupported DOM hacks and copying old OWL patterns.
- Register required JS/CSS/XML in the proper `__manifest__.py` asset bundle (for example, `web.assets_backend` for backend components).
- For QWeb PDF reports, prefer CSS/layout techniques compatible with the configured PDF engine; do not assume all Bootstrap 5 CSS features render in wkhtmltopdf.
- Verify third-party addon compatibility rather than assuming prior Odoo versions are compatible.

## Code Style & Naming

- Use one file per primary model group; model dots become underscores.
  - `example.record` -> `models/example_record.py`.
  - `library.book` -> `models/library_book.py`.
  - Inheritance of `res.partner` -> `models/res_partner.py`.
- Name view files `views/<model_name>_views.xml`.
- Name security CSV `security/ir.access.csv` (Odoo 20).
- Use descriptive XML IDs such as `example_record_view_form`, `example_record_view_list`, and `example_record_action`.
- Follow local naming conventions in existing modules; do not rename existing files or XML IDs without a real reason.
- Keep imports clean and order them consistently; avoid unnecessary dependencies.
- Follow `ruff.toml` and the local project style over generic assistant preferences.

## Checklist for New Models, Views & Features

1. Add Python files to `models/__init__.py`, `wizard/__init__.py`, or `controllers/__init__.py` as appropriate; ensure the addon root imports those packages.
2. Add Odoo 20 `ir.access` permissions/restrictions for new persistent and transient models as needed; review group-based record visibility.
3. Include new data/XML/CSV in `__manifest__.py`, with dependencies loaded before consumers:
   - groups and other prerequisite security data,
   - `security/ir.access.csv`,
   - sequences and other initial data,
   - wizard and model views,
   - QWeb templates/report actions,
   - menus after their referenced actions.
4. Add frontend code to the correct `assets` bundle when applicable.
5. Verify that inherited views, field names, XML IDs, and object methods exist in the current Odoo 20 source.
6. Include tests covering the business flow, negative cases, and security where practical.
7. Upgrade/install only on an explicitly selected disposable or development database.

The loading order is dependency-sensitive, not a rigid universal folder ordering. Check each XML reference and its declaration.

## Verification Before Finishing

- Read affected files and relevant Odoo 20 core source before changing behavior.
- Restrict the diff to the task and `custom_addons/`.
- Validate Python syntax and run focused Ruff checks.
- Validate XML syntax, referenced fields, XML IDs, actions, and menu targets.
- Inspect `__manifest__.py` dependencies and asset/data lists.
- Validate `ir.access` permissions and restrictions using representative non-admin users.
- Run relevant Odoo module tests on a non-production database when permitted.
- Check the result in Odoo UI or QWeb PDF if that behavior changed and a test environment is available.
- Run `git diff --check` and review the actual diff.
- Report what changed, what was tested, what could not be tested, and any compatibility risks.
- Never state that tests passed unless they were actually run and passed.

## Database, Migration & Safety Rules

- Never execute data deletion, `DROP`, `TRUNCATE`, mass `unlink()`, or destructive scripts without explicit approval.
- Never migrate, initialize, install, update, or modify a production database without explicit approval.
- Never change PostgreSQL roles, database ownership, or server settings as an unrequested side effect.
- Require a backup and a rollback plan before database migration.
- Migration of **custom addon source code** and migration of the **database/data** are separate tasks.
- Do not assume an Odoo 18 database can simply be opened with the Odoo 20 server.
- Perform migration on a copy first; confirm the exact supported upgrade route and tool for the installation (Community vs Enterprise).
- Do not print, commit, or hardcode passwords, tokens, secret keys, or real customer data.
- Ask for confirmation before external API calls or commands with material data effects.

## Git Commit Conventions

- Never add `Co-Authored-By: Claude`, `Generated with Claude Code`, or other AI attribution trailers.
- Write commit messages as if authored by the project developer.
- Follow Odoo style: `[TAG] <module>: short imperative description`.
- Tags:
  - `[FIX]`: bug fix.
  - `[ADD]`: new module or feature.
  - `[IMP]`: incremental improvement.
  - `[REF]`: major refactor.
  - `[REM]`: removal of unused code.
  - `[MOV]`: moved files (use `git mv` when appropriate).
  - `[REV]`: revert.
- Prefer concise subjects (target under 50 characters where practical); add a body for non-trivial changes explaining **why**.
- Examples:
  - `[ADD] example: add record management workflow`
  - `[FIX] example: correct inherited view xpath`
  - `[IMP] example: validate scheduling conflicts`
- Do not commit, amend, or push unless the user requests it.

## Reference Priority

1. Actual local Odoo 20.0 source in this checkout.
2. Official Odoo 20.0 developer docs: https://www.odoo.com/documentation/20.0/developer.html
3. Existing compatible official Odoo 20 addons and tests.
4. OCA or third-party code verified to target Odoo 20; treat it as secondary evidence.

When instructions conflict with proven Odoo 20 behavior, explain the discrepancy and use the verified local implementation. Do not invent non-existent APIs or silently fall back to old-version patterns.
