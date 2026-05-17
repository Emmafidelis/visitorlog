# Visitor Management System

## Business Summary

Visitor Management System is a Frappe app for recording visitors, assigning visitor cards or QR badges, and tracking check-in and check-out activity. It is intended for reception, front-office, security, and administration teams that need a structured record of who entered the premises, who they came to meet, why they visited, and when they left.

The app replaces paper visitor books or ad hoc spreadsheets with Frappe DocTypes, role-based records, timestamped logs, and API methods that can support scanner, kiosk, or mobile registration flows.

The app is packaged as a Frappe app named `visitor`. It does not declare ERPNext as a required dependency in `hooks.py`, but it does reference the `Employee` DocType for host selection. Standalone use without ERPNext or HRMS should be tested before production.

## Business Problems This App Solves

| Problem | How the App Helps |
| --- | --- |
| Visitor records are kept in paper books or spreadsheets | Stores visitor details in searchable Frappe records. |
| Reception teams cannot easily tell whether a visitor card is already in use | Checks active `IN` logs before assigning or reusing a QR card. |
| Exit times are missed or recorded inconsistently | Scanner logic can mark active cards as signed out and set `time_out`. |
| Host and purpose information is not consistently captured | Visitor and log records include host, purpose, contact, company, and visit date fields. |
| Management lacks a basic visitor audit trail | `Visitors Registration Log` records preserve entry and exit history. |

## Who This App Is For

- Offices, schools, hospitals, warehouses, and facilities with a staffed reception or security desk.
- Organizations that issue reusable visitor badges or QR cards.
- Frappe or ERPNext sites that want visitor registration in the same system as employee or host data.
- Teams planning a scanner, kiosk, Flutter, or mobile check-in experience backed by Frappe APIs.

## Who This App Is Not For

- Organizations that need full access-control hardware integration out of the box.
- Sites that require prebuilt dashboards, analytics reports, or visitor approval workflows without customization.
- Pure Frappe deployments where no `Employee` DocType or equivalent host model is available, unless the Employee dependency is adjusted.
- Environments that need advanced compliance, identity verification, watchlist screening, or badge printing already built in.

## Business Benefits

| Benefit | Business Impact |
| --- | --- |
| Centralized visitor records | Reduces scattered logs and improves lookup during audits or incidents. |
| QR card tracking | Helps prevent one reusable visitor card from being assigned to multiple active visitors. |
| Host and purpose capture | Gives reception and security teams clearer context for each visit. |
| Entry and exit timestamps | Improves visibility into who is currently on site. |
| API-ready design | Enables scanner, mobile app, or kiosk workflows to connect to Frappe. |
| Role-based Frappe permissions | Lets administrators control who can manage visitor records. |

## Before and After

| Before | After |
| --- | --- |
| Visitors sign a paper book or spreadsheet. | Reception creates a `Visitor` or `Visitors Registration Log` record. |
| Cards are handed out without reliable active-use checks. | The scan API checks whether a QR card already has an active `IN` log. |
| Exit times depend on manual follow-up. | Scanning an active card can mark the log `OUT` and set `time_out`. |
| Visitor details are hard to search later. | Visitor records and logs are stored as Frappe DocTypes. |
| Host information may be informal. | Host fields link to `Employee` where available. |

## Typical Use Cases

- Register a visitor before or at arrival.
- Assign a reusable QR visitor card.
- Check whether a card is available or currently in use.
- Sign out a visitor by scanning their assigned card.
- Retrieve recent visitor logs with optional date and status filters.
- Provide a mobile app with host employee options for visitor registration.

## Example Business Workflow

1. An administrator creates reusable `Visitors Registration Card` records for physical visitor badges.
2. A receptionist captures visitor details, purpose, host employee, and contact information.
3. The visitor is assigned a card or QR code.
4. The system records the visitor as checked in through a `Visitors Registration Log`.
5. When the visitor leaves, the card is scanned.
6. The system marks the active log as `OUT` and records the exit time.
7. Reception or management can review visitor activity later from Frappe records or API responses.

## ERPNext Value Addition

The app appears designed to work best when an `Employee` DocType is available.

| ERPNext / HR Data | Evidence | Value |
| --- | --- | --- |
| `Employee` | `Visitor.host_employee` and `Visitors Registration Log.employee` are Link fields to `Employee`. | Lets visitors be connected to the employee or host they are visiting. |
| Active employees | `get_employees` reads active Employee records when the DocType exists. | Supports host selection in scanner, kiosk, or mobile registration interfaces. |

To confirm: whether the intended production dependency is ERPNext, HRMS, or a custom `Employee` DocType.

## Stand-alone Value

The package does not declare `required_apps = ["erpnext"]`, and the API method `get_employees` includes a fallback to system users if the `Employee` DocType is not found. That suggests partial standalone intent.

However, the main `Visitor` DocType requires `host_employee` as a Link to `Employee`, and its controller validates that the linked employee exists. A pure Frappe-only installation should be tested and may need customization to make host selection user-based instead of employee-based.

## Decision Guide

| Question | Good Fit If Yes |
| --- | --- |
| Do you currently use paper books or spreadsheets for visitors? | Yes |
| Do you issue reusable visitor badges or QR cards? | Yes |
| Do you need basic entry and exit tracking? | Yes |
| Do you want visitor records inside Frappe or ERPNext? | Yes |
| Do you need host selection from Employee records? | Yes |
| Do you need complex approvals, hardware gate control, or analytics dashboards immediately? | This app may need customization |

## Expected Business Outcomes

The app can help improve visitor accountability, reception consistency, and access-log visibility. It gives teams a practical foundation for moving visitor registration into Frappe and integrating that process with scanners or mobile clients.

Actual outcomes will depend on reception adoption, card-handling discipline, permission setup, and whether the Employee/host model matches the organization.

## Screenshots / Visual Walkthrough

To confirm before publishing:

- Visitor registration form screenshot
- Visitor card list screenshot
- Visitor log list screenshot
- Scanner, kiosk, or mobile app screenshots if available

## Demo Scenario

1. Create a visitor card named from the `VRC-.YYYY.-` naming series.
2. Register a visitor with name, phone, email, company, purpose, and host employee.
3. Create or assign a `Visitors Registration Log` with `log_type = IN`.
4. Call the scan endpoint with the card QR code.
5. Confirm the active log changes to `OUT` and receives a `time_out` value.

## Implementation Effort

| Area | Effort | Notes |
| --- | --- | --- |
| Frappe app installation | Low | Standard bench app installation. |
| Employee/host setup | Medium | Requires confirming whether ERPNext, HRMS, or a custom Employee DocType is available. |
| Card setup | Low | Create `Visitors Registration Card` records for physical badges. |
| Scanner or mobile integration | Medium | Whitelisted APIs exist, but clients must be configured and tested. |
| Permissions review | Medium | Current DocType permissions allow both `System Manager` and `Employee` broad access. |
| Reporting and dashboards | Medium | No custom reports or dashboards are present in the repository. |
| Production hardening | Medium | Authentication, retention, privacy, and operational procedures should be confirmed. |

## What Needs to Be Ready Before Implementation

- A Frappe bench and site.
- A decision on whether ERPNext, HRMS, or another Employee source will be used.
- Reception or security users and their roles.
- Physical visitor badges or QR-card naming conventions.
- A process for who creates visitor records and who signs visitors out.
- Retention rules for visitor contact details and photos.
- API authentication approach for scanner, kiosk, or mobile clients.

## Risks and Considerations

- The app references `Employee` but does not declare ERPNext or HRMS as a required app.
- Current permissions grant broad create, write, delete, export, and share access to `Employee` role users.
- `register_visitor` is defined twice in `visitor/api/visitor_scan.py`; in Python, the second definition overrides the first at import time.
- No custom reports, dashboards, workflows, fixtures, or background jobs are present.
- Visitor photos and contact details may be sensitive personal data.
- APIs use `ignore_permissions=True` in some write paths, so endpoint access control should be reviewed before exposure.

## Frequently Asked Business Questions

### Do we need ERPNext?

To confirm. The app does not declare ERPNext as a dependency, but it uses the `Employee` DocType for host fields and employee lookup. It appears best suited for ERPNext, HRMS, or another Frappe site where `Employee` exists.

### Will this replace ERPNext?

No. It is a visitor-management app that can run inside a Frappe/ERPNext environment. It does not replace ERP, HR, accounting, inventory, or payroll functions.

### Can it be customized?

Yes. It is a standard Frappe app with DocTypes, controllers, and whitelisted Python API methods.

### Can managers get reports?

Basic list views and filtered API responses are available through Frappe records. Custom reports or dashboards are not included in the repository and would need to be built if required.

### Can existing visitor spreadsheet data be migrated?

Likely yes through Frappe data import or migration scripts, but no migration tooling is included in this repository.

### What should we prepare before implementation?

Prepare employee or host data, visitor badge numbers, user roles, privacy rules, and the physical reception workflow.

---

## Key Features

- Visitor profile registration with name, email, phone, company, photo, purpose, host, visit date, and status.
- Reusable visitor card records using the `VRC-.YYYY.-` naming series.
- Visitor registration logs using the `VRL-.YYYY.-` naming series.
- Automatic `full_name` generation for `Visitor`.
- Automatic check-in and check-out timestamp logic in controllers.
- QR/card scan API for card availability, sign-in, and sign-out flows.
- Employee lookup API with fallback formatting from system users.
- Visitor log retrieval API with optional log type and date filters.

## Compatibility

| Component | Evidence |
| --- | --- |
| Frappe | App uses Frappe DocTypes, controllers, hooks, and whitelisted methods. Exact supported Frappe version is to confirm. |
| ERPNext / HRMS | No declared dependency, but `Employee` is referenced in DocTypes and APIs. |
| Python | `pyproject.toml` requires Python `>=3.10`. |
| Packaging | Uses `flit_core >=3.4,<4`. |
| JavaScript assets | No app JavaScript assets found; pre-commit includes ESLint and Prettier if JS is added later. |

## App Mode

`ERPNext optional / conditional integration - to confirm`

The repository does not declare ERPNext in `required_apps`, and `get_employees` has a fallback path. At the same time, the main visitor workflow references `Employee`, so production readiness without ERPNext or HRMS is not guaranteed from the current code.

## Installation

Install into a Frappe bench:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench --site your-site-name install-app visitor
bench --site your-site-name migrate
```

If the app is already present in `apps/visitor`:

```bash
cd $PATH_TO_YOUR_BENCH
bench --site your-site-name install-app visitor
bench --site your-site-name migrate
```

To confirm: the canonical repository URL, default branch, and supported Frappe/ERPNext versions.

## Configuration

1. Confirm the app appears in the Frappe Desk module list.
2. Confirm whether `Employee` exists on the site.
3. Create `Visitors Registration Card` records for reusable badges.
4. Assign appropriate roles to reception, security, and administrators.
5. Review DocType permissions before giving broad access to all employees.
6. Configure scanner, kiosk, or mobile clients to call the API endpoints.
7. Test card assignment, active-card detection, and sign-out behavior.

## Usage

### Registering Visitors

Use the `Visitor` DocType or API endpoint to capture visitor details, host, purpose, and visit date.

### Managing Cards

Create `Visitors Registration Card` records for each reusable physical card or QR badge. The card record name is used as the QR code value by the scan logic.

### Tracking Entry and Exit

Use `Visitors Registration Log` records to track operational check-in and check-out activity. A log with `log_type = IN` represents an active visitor on site. Changing or scanning it to `OUT` records the exit time.

## Modules and DocTypes

| Module | DocType | Purpose | Evidence |
| --- | --- | --- | --- |
| Visitor | `Visitor` | Stores visitor profile and visit status details. | `visitor/visitor/doctype/visitor/visitor.json` |
| Visitor Registration | `Visitors Registration Card` | Stores reusable card or QR badge labels. | `visitor/visitor_registration/doctype/visitors_registration_card/visitors_registration_card.json` |
| Visitor Registration | `Visitors Registration Log` | Stores entry and exit logs. | `visitor/visitor_registration/doctype/visitors_registration_log/visitors_registration_log.json` |
| Visitor | `Visitors Registration Card` and `Visitors Registration Log` copies | Additional DocType files also exist under the `Visitor` module path. | `visitor/visitor/doctype/` |

## ERPNext Integration Details

| Integration Point | Behavior |
| --- | --- |
| `Employee` Link fields | `Visitor.host_employee` and `Visitors Registration Log.employee` link to `Employee`. |
| Employee validation | `Visitor.validate` checks whether the selected employee exists. |
| Employee list API | `get_employees` reads active Employee records if the DocType exists. |
| Fallback behavior | `get_employees` falls back to enabled system users if no Employee DocType is found. |

No Sales, Purchase, Stock, Accounting, Project, CRM, or Payroll integrations were found.

## Custom Fields and Fixtures

No `fixtures/` directory or custom field fixtures were found in the repository.

## Permissions

The DocTypes grant broad permissions to:

| Role | Access Shown in DocType JSON |
| --- | --- |
| `System Manager` | Create, read, write, delete, print, email, export, report, share. |
| `Employee` | Create, read, write, delete, print, email, export, report, share. |

Review these permissions before production. Many organizations will want narrower roles for reception, security, HR, and administrators.

## Reports and Dashboards

No custom report, dashboard, workspace, chart, or number card files were found in the repository.

Users can still use standard Frappe list views and filters on `Visitor` and `Visitors Registration Log`.

## APIs

Whitelisted methods are defined in `visitor/api/visitor_scan.py`.

| Method | Purpose | Important Parameters |
| --- | --- | --- |
| `visitors_scan` | Handles scan, register-check, and search/sign-in flows for QR cards. | `qr_code`, `api_type`, `log_name` |
| `create_visitor_log` | Creates an `IN` visitor log. | `full_name`, `contact_number`, `address`, `purpose`, `employee`, `qr_code` |
| `get_visitor_status` | Checks whether a card exists and whether a visitor is currently in. | `qr_code` |
| `register_visitor` | Creates a `Visitor` record and returns badge information. | `first_name`, `last_name`, `email_address`, `phone_number`, `company_organization`, `purpose`, `host_employee`, `expected_duration`, `visit_date`, `status` |
| `get_employees` | Returns active employees, or system-user fallback data. | none |
| `get_visitor_logs` | Returns recent visitor logs with optional filtering. | `limit`, `log_type`, `date_from`, `date_to` |

Endpoint format:

```text
/api/method/visitor.api.visitor_scan.get_visitor_status
```

Example `get_visitor_status` parameter:

```text
qr_code=VRC-2025-0001
```

## Hooks and Events

Active app metadata in `visitor/hooks.py`:

| Hook / Setting | Status |
| --- | --- |
| `app_name` | `visitor` |
| `app_title` | `Visitor Management System` |
| `app_publisher` | `Aakvatech` |
| `app_license` | `mit` |
| `required_apps` | Not active |
| `fixtures` | Not active |
| `doc_events` | Not active |
| `scheduler_events` | Not active |
| `app_include_js` / `app_include_css` | Not active |
| install/uninstall hooks | Not active |

DocType controller behavior:

- `Visitor.before_save` builds `full_name` and sets check-in/check-out times based on status.
- `Visitor.validate` validates email, phone number, and host employee.
- `VisitorsRegistrationLog.before_save` sets `time_in` or `time_out` based on `log_type`.

## Background Jobs

No active scheduled jobs or background workers were found.

## Developer Setup

```bash
cd $PATH_TO_YOUR_BENCH/apps/visitor
pre-commit install
bench --site your-site-name migrate
bench --site your-site-name clear-cache
```

Development tooling:

- Ruff linting and formatting
- Prettier and ESLint hooks for JavaScript files if added
- Python 3.10 or newer
- Frappe managed by bench

## Project Structure

```text
visitor/
  api/
    visitor_scan.py
  visitor/
    doctype/
      visitor/
      visitors_registration_card.json
      visitors_registration_card.py
      visitors_registration_log/
  visitor_registration/
    doctype/
      visitors_registration_card/
      visitors_registration_log/
  hooks.py
  modules.txt
  patches.txt
```

## Migration Notes

`visitor/patches.txt` is present but contains no active pre-model-sync or post-model-sync patches.

No migration scripts for importing legacy visitor logs were found.

## Upgrade Guide

For normal Frappe app upgrades:

```bash
cd $PATH_TO_YOUR_BENCH/apps/visitor
git pull
cd $PATH_TO_YOUR_BENCH
bench --site your-site-name migrate
bench --site your-site-name clear-cache
```

Before upgrading production, test visitor registration, card scanning, and sign-out flows on a staging site.

## Uninstallation

No custom uninstall hooks were found. Use the standard Frappe uninstall process only after backing up visitor records:

```bash
bench --site your-site-name uninstall-app visitor
```

## Troubleshooting

| Symptom | What to Check |
| --- | --- |
| Host employee cannot be selected | Confirm the `Employee` DocType exists and has active records. |
| Card shows as already in use | Check for an active `Visitors Registration Log` with `log_type = IN` and the same `qr_code`. |
| Scan returns `card_not_existing` | Confirm the QR code matches an existing `Visitors Registration Card` record name. |
| Visitor registration fails | Check required fields, email format, phone number, and host employee validity. |
| Mobile employee list is empty | Confirm Employee records exist or that enabled system users are available for fallback. |

## Security

- Review API access before connecting external scanner, kiosk, or mobile clients.
- Several API write paths use `ignore_permissions=True`; protect endpoints with authentication and role checks appropriate to your deployment.
- Review broad `Employee` role permissions before production.
- Define retention rules for visitor contact details, images, and visit history.
- Use HTTPS for API clients.

## Repository Evidence Reviewed

| File / Area | Evidence Found |
| --- | --- |
| `pyproject.toml` | App package name is `visitor`; Python requirement is `>=3.10`; publisher is Aakvatech. |
| `visitor/hooks.py` | App title, publisher, description, email, and MIT license metadata; no active required apps, fixtures, scheduled jobs, or doc events. |
| `visitor/modules.txt` | Defines the `Visitor` module. |
| `visitor/patches.txt` | Patch sections exist but no active patches are listed. |
| `visitor/visitor/doctype/visitor/visitor.json` | Defines visitor profile, contact, visit, host, and status fields. |
| `visitor/visitor/doctype/visitor/visitor.py` | Builds full name, timestamps status changes, and validates email, phone, and employee. |
| `visitor/visitor_registration/doctype/visitors_registration_card/` | Defines reusable visitor card records. |
| `visitor/visitor_registration/doctype/visitors_registration_log/` | Defines visitor entry/exit log records and timestamp behavior. |
| `visitor/api/visitor_scan.py` | Defines scan, registration, employee lookup, status, and log retrieval APIs. |
| `.pre-commit-config.yaml` | Defines Ruff, Prettier, ESLint, and standard pre-commit hooks. |

## To Confirm Before Publishing

- Supported Frappe version and whether Frappe v15 is the target.
- Whether ERPNext, HRMS, or another Employee provider is required.
- Canonical repository URL and default branch for installation commands.
- Whether duplicate `register_visitor` definitions are intentional.
- Whether duplicate DocType files under `visitor/visitor/doctype` and `visitor/visitor_registration/doctype` are intentional.
- Screenshots and demo video availability.
- Production permission model for reception, security, Employee, and System Manager users.
- Data retention policy for visitor images and contact details.
- Whether badge printing, notifications, reports, or dashboards are planned.

## Support and Maintenance

Maintainer information from project metadata:

| Field | Value |
| --- | --- |
| Publisher | Aakvatech |
| Email | `info@aakvatech.com` |

To confirm: issue tracker, support policy, release cadence, and production support channel.

## Contributing

Install pre-commit before contributing:

```bash
cd apps/visitor
pre-commit install
```

Pre-commit is configured for:

- Ruff
- ESLint
- Prettier
- pyupgrade-compatible checks through Ruff rules
- Standard file and syntax checks

## Versioning

The package uses dynamic versioning in `pyproject.toml`.

To confirm: release tags, changelog format, and compatibility matrix.

## License

MIT. See [license.txt](license.txt).

## Maintainers

- Aakvatech
- `info@aakvatech.com`
