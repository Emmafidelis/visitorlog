# Visitor Management System

## Business Summary

Visitor Management System is a Frappe app for recording visitors, verifying their ID via OCR, assigning QR badges, and tracking check-in and check-out activity. It is intended for reception, front-office, security, and administration teams that need a structured, auditable record of who entered the premises, who they came to meet, why they visited, and when they left.

The app replaces paper visitor books or ad hoc spreadsheets with Frappe DocTypes, role-based permissions, a badge assign/scan state machine, mandatory human ID verification, and API methods that support scanner, kiosk, or mobile registration flows.

The app is packaged as a Frappe app named `visitor`. It does not declare ERPNext as a required dependency in `hooks.py`, but it does reference the `Employee` DocType for host selection. It has been tested on a Frappe v15 site with ERPNext and HRMS installed.

## Business Problems This App Solves

| Problem | How the App Helps |
| --- | --- |
| Visitor records are kept in paper books or spreadsheets | Stores visitor details in searchable Frappe records. |
| Anyone can walk in and get checked in without ID verification | OCR-assisted ID capture plus a mandatory human-verification gate blocks check-in until a person confirms the scanned ID. |
| Reception teams cannot easily tell whether a badge is already in use | `Visitors Registration Card.status`/`current_visitor` is the single source of truth for badge availability; double-booking a badge is blocked. |
| Exit times are missed or recorded inconsistently | The same badge scan that checked a visitor IN closes that exact log row on the next scan and releases the badge automatically. |
| Host and purpose information is not consistently captured | Visitor and log records include host, purpose, contact, company, and visit date fields. |
| Management lacks a visitor audit trail | `Visitors Registration Log` preserves entry/exit history, and the Visitor Audit Trail report surfaces every field-level change (who scanned, who verified, when) via Frappe's built-in version tracking. |
| ID photos and OCR data need to stay private | Scanned ID images are forced private server-side regardless of upload settings; `id_number`/`scanned_id_image`/`ocr_raw_text` are restricted to System Manager and Visitor Verifier roles via permlevel. |

## Who This App Is For

- Offices, schools, hospitals, warehouses, and facilities with a staffed reception or security desk.
- Organizations that need ID verification before granting premises access, not just a sign-in book.
- Organizations that issue reusable visitor badges or QR cards.
- Frappe or ERPNext sites that want visitor registration in the same system as employee or host data.
- Teams planning a scanner, kiosk, Flutter, or mobile check-in experience backed by Frappe APIs.

## Who This App Is Not For

- Organizations that need full access-control hardware integration (turnstiles, biometric readers) out of the box.
- Pure Frappe deployments where no `Employee` DocType or equivalent host model is available, unless the Employee dependency is adjusted.
- Environments that need cloud-based OCR out of the box — the default OCR backend is local/offline (Tesseract); a cloud backend would need to be added.
- Environments that need watchlist screening or automatic badge printing/label design — not built in.

## Business Benefits

| Benefit | Business Impact |
| --- | --- |
| OCR-assisted ID capture + mandatory verification | Reduces manual typing while still requiring a human to confirm identity before check-in — no silent bypass path. |
| Centralized visitor records | Reduces scattered logs and improves lookup during audits or incidents. |
| Badge state machine (Available/Assigned/Lost/Damaged/Disabled) | Prevents one badge being double-booked to two active visitors; makes lost/damaged badges explicit. |
| Entry and exit timestamps | Improves visibility into who is currently on site. |
| Field-level audit trail | Every OCR/verification/status change is versioned and reportable without extra bookkeeping code. |
| API-ready design | Enables scanner, mobile app, or kiosk workflows to connect to Frappe. |
| Role-based permissions incl. `Visitor Verifier` | Separates "who can see a visitor is on site" from "who can see their ID photo and number." |

## Typical Use Cases

- Register a visitor, scan their ID, and have OCR pre-fill the form for review.
- Verify the OCR-extracted ID details, then assign an available badge.
- Scan the badge at the gate to check the visitor IN, then scan again on exit to check them OUT and release the badge.
- Look up whether a badge is currently in use, and by whom.
- Run reports on who's currently on-site, daily traffic, host load, unreturned badges, and OCR exceptions.
- Provide a mobile app or kiosk with host employee options for visitor pre-registration (no ID scan involved).

## Example Business Workflow

1. An administrator creates reusable `Visitors Registration Card` records for physical badges (status defaults to `Available`).
2. A receptionist registers the visitor in the `Visitor` form, purpose, and host employee, then clicks **Scan ID** to capture and OCR-read their ID.
3. The receptionist reviews the OCR-extracted fields (correcting anything wrong) and saves.
4. A `Visitor Verifier` (or System Manager) clicks **Verify ID** to confirm the details match the physical document — this is the only action that can set `ocr_verified`.
5. Reception assigns an available badge to the now-verified visitor.
6. Security scans the badge at the gate — first scan checks the visitor IN and stamps `check_in_time`.
7. When the visitor leaves, the same badge is scanned again — this closes the same log row, stamps `check_out_time`, and releases the badge back to `Available`.
8. Reports (Current Visitors In Premises, Daily Visitor Log, Unreturned Badge Report, Visitor by Host Employee, OCR Exception Report, Visitor Audit Trail) give reception and management visibility without extra work.

## ERPNext Value Addition

| ERPNext / HR Data | Evidence | Value |
| --- | --- | --- |
| `Employee` | `Visitor.host_employee` and `Visitors Registration Log.employee` are Link fields to `Employee`. | Lets visitors be connected to the employee or host they are visiting. |
| Active employees | `get_employees` reads active Employee records when the DocType exists. | Supports host selection in scanner, kiosk, or mobile registration interfaces. |

## Stand-alone Value

The package does not declare `required_apps = ["erpnext"]`, and `get_employees` falls back to enabled system users if the `Employee` DocType is not found. However, `Visitor.host_employee` is a required Link to `Employee` and the controller validates it exists, so a pure Frappe-only installation needs the host-selection logic adjusted before it will work without ERPNext/HRMS.

## Decision Guide

| Question | Good Fit If Yes |
| --- | --- |
| Do you currently use paper books or spreadsheets for visitors? | Yes |
| Do you need to verify a visitor's ID before letting them in, not just log a name? | Yes |
| Do you issue reusable visitor badges or QR cards? | Yes |
| Do you need basic entry and exit tracking with an audit trail? | Yes |
| Do you want visitor records inside Frappe or ERPNext? | Yes |
| Do you need host selection from Employee records? | Yes |
| Do you need cloud OCR, biometric hardware, or badge-printing hardware integration out of the box? | This app needs customization |

## Implementation Effort

| Area | Effort | Notes |
| --- | --- | --- |
| Frappe app installation | Low | Standard bench app installation. |
| Employee/host setup | Medium | Requires ERPNext, HRMS, or a custom Employee DocType. |
| OCR setup | Low–Medium | Tesseract (default) needs the `tesseract-ocr` system package installed; PaddleOCR is an optional, heavier install for better accuracy. |
| Card setup | Low | Create `Visitors Registration Card` records for physical badges. |
| Scanner or mobile integration | Medium | Whitelisted APIs exist for the legacy quick-checkin flow; the primary flow is the Desk form + `visitor.api.badge` endpoints. |
| Permissions review | Low | `Visitor Verifier` role plus permlevel restrictions on ID fields are already configured — review against your org's actual roles. |
| Production hardening | Medium | Retention policy for ID images/OCR text should be decided per deployment; consider PaddleOCR only if the server has RAM/CPU headroom. |

## Risks and Considerations

- The app references `Employee` but does not declare ERPNext or HRMS as a required app.
- The default OCR backend (Tesseract) needs the `tesseract-ocr` binary installed on the server — `pip install pytesseract` alone is not enough.
- PaddleOCR is a heavy install (its own ML runtime); only enable it in `Visitor Settings` on a server with spare RAM/CPU.
- OCR field extraction (`id_number`/`first_name`/`middle_name`/`last_name`) is best-effort regex matching, not a certified ID-parsing engine — this is why human verification is mandatory before check-in, not optional. It assumes given-name-first ordering; a passport data page or MRZ line that prints surname first can come out with first/last name swapped, which the reviewer is expected to catch and correct before verifying.
- The legacy `visitors_scan`/`create_visitor_log` endpoints are kept for backward compatibility with any existing scanner/kiosk/mobile integrations, but `create_visitor_log` now requires the visitor to already exist and be ID-verified from a prior visit — a brand-new visitor cannot be checked in through that endpoint without going through ID verification first.
- Visitor contact details and ID data are sensitive personal data; define a retention/purge policy for your deployment (not built in).
- The **Scan ID** dialog's native Camera button (Frappe's `allow_take_photo` uploader option) only appears over a secure origin — HTTPS, or `localhost` — because browsers don't expose `navigator.mediaDevices` on plain HTTP. On an HTTP-only deployment, users can still attach an ID photo via "My Device" (which falls back to the OS's own camera/gallery picker on most phones), but the in-app capture UI needs HTTPS to show up.
- **If installing on a site that already has visitor data** (this app shipped with zero pre-existing rows on its first deployment, so this path is untested): any `Visitors Registration Log` row left open (`log_type=IN`, no `time_out`) from before this upgrade has no matching `Visitors Registration Card.status="Assigned"`, since that field is new. A gate scan of that visitor's badge will hit the "badge not assigned to anyone" branch instead of closing their visit. Manually reconcile open pre-upgrade logs (set the matching Card's `status`/`current_visitor`) before relying on `scan_badge` for those visitors.

## Frequently Asked Business Questions

### Do we need ERPNext?

The app does not declare ERPNext as a dependency, but it uses the `Employee` DocType for host fields and employee lookup. It is best suited for ERPNext, HRMS, or another Frappe site where `Employee` exists.

### Does OCR replace manual verification?

No — by design. OCR only pre-fills the form. `Visitor.ocr_verified` is a read-only field that can only be set via the `mark_verified` method (role-gated to System Manager / Visitor Verifier), and the server blocks `status = "Checked In"` for any visitor whose ID hasn't been verified, regardless of how the save request is made.

### Can managers get reports?

Yes — six reports ship with the app: Current Visitors In Premises, Daily Visitor Log, Unreturned Badge Report, Visitor by Host Employee, OCR Exception Report, and Visitor Audit Trail. They're linked from the "Visitors" workspace.

### What should we prepare before implementation?

Employee/host data, visitor badge numbering, user roles (who gets `Visitor Verifier`), a retention policy for ID images, and — if using the default OCR backend — the `tesseract-ocr` system package on the server.

---

## Key Features

- Visitor profile registration with name, email, phone, company, photo, purpose, host, visit date, and status.
- OCR-assisted ID capture (**Scan ID** button) with a pluggable backend (Tesseract by default, PaddleOCR as an opt-in upgrade).
- Mandatory human ID verification (**Verify ID**) before a visitor can be checked in — enforced server-side in `Visitor.validate()`, not just in the UI.
- Badge state machine: `Available → Assigned → Available` via `visitor.api.badge.assign_badge` / `scan_badge`, with `Lost`/`Damaged`/`Disabled` states for administrative use.
- Duplicate-visitor warning by ID number when registering a new visitor.
- Private-by-default storage for scanned ID images, enforced server-side regardless of upload settings.
- Permlevel-restricted ID fields (`scanned_id_image`, `ocr_raw_text`, `ocr_suggested_json`, `id_number`) — visible only to System Manager / Visitor Verifier.
- Six built-in reports covering premises occupancy, daily traffic, host load, unreturned badges, OCR exceptions, and a full audit trail.
- Legacy QR/card scan API kept for existing scanner, kiosk, or mobile integrations.

## Compatibility

| Component | Notes |
| --- | --- |
| Frappe | Tested on Frappe v15 (15.113.2). |
| ERPNext / HRMS | No declared dependency, but `Employee` is referenced in DocTypes and APIs; tested with both installed. |
| Python | `pyproject.toml` requires Python `>=3.10`. |
| OCR | `tesseract-ocr` system package (default backend) + `pytesseract`, `opencv-python-headless` (Python deps). `paddleocr` is an optional extra. |
| Packaging | Uses `flit_core >=3.4,<4`. |

## Installation

Install into a Frappe bench:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench --site your-site-name install-app visitor
bench --site your-site-name migrate
```

If the app is already present in `apps/visitor`:

```bash
cd $PATH_TO_YOUR_BENCH
bench --site your-site-name install-app visitor
bench --site your-site-name migrate
```

Install the OCR system dependency (default Tesseract backend):

```bash
sudo apt-get install -y tesseract-ocr
```

**On Frappe Cloud**, you don't get shell/`apt-get` access — instead, `pyproject.toml` declares this under `[deploy.dependencies.apt]`, and Frappe Cloud installs it automatically on every deploy of this app. If you're seeing `pytesseract.pytesseract.TesseractNotFoundError` on a Frappe Cloud site, trigger a fresh deploy of a bench/release that includes this `pyproject.toml` (App → your bench → **New Release** / redeploy); manually installing packages via SSH on Frappe Cloud does not persist across deploys, only this file does.

To use PaddleOCR instead (higher accuracy, heavier install — only do this on a server with spare RAM/CPU):

```bash
./env/bin/pip install "visitor[paddleocr]"
```
Then select "PaddleOCR (Local)" in **Visitor Settings**.

## Configuration

1. Confirm the app appears in the Frappe Desk module list.
2. Confirm the `Employee` DocType exists and has active records.
3. Open **Visitor Settings** and confirm the OCR backend, confidence threshold, and orphan-exit-scan policy.
4. Create `Visitors Registration Card` records for reusable badges.
5. Assign the `Visitor Verifier` role to reception/security staff who should review and confirm scanned IDs.
6. Test the full flow: register → scan ID → verify → assign badge → scan IN → scan OUT.

## Usage

### Registering and Verifying Visitors

Open the `Visitor` form, fill in personal/visit details, click **Scan ID** to capture and OCR-read the visitor's ID (camera or file upload), review/correct the extracted fields, and Save. Once saved, a `Visitor Verifier` or System Manager clicks **Verify ID** to confirm the details match the physical document.

### Managing Badges

Create `Visitors Registration Card` records for each reusable physical badge. Use `visitor.api.badge.assign_badge(visitor, qr_code)` to link a verified visitor to an available badge, then `visitor.api.badge.scan_badge(qr_code)` at the gate — the first scan checks the visitor IN, the next scan of the same badge checks them OUT and releases it.

### Tracking Entry and Exit

`Visitors Registration Log` records the movement history. A row with `log_type = IN` and no `time_out` represents an active visitor on site; `scan_badge` closes that same row to `OUT` rather than creating a new one.

## Modules and DocTypes

| Module | DocType | Purpose |
| --- | --- | --- |
| Visitor | `Visitor` | Visitor profile, visit status, and ID verification fields. |
| Visitor | `Visitors Registration Card` | Reusable badge/card records with an availability state machine. |
| Visitor | `Visitors Registration Log` | Entry/exit movement log, linked to `Visitor` and `Visitors Registration Card`. |
| Visitor | `Visitor Settings` | Single DocType: OCR backend selection, confidence threshold, orphan-exit-scan policy. |

## Permissions

| Role | Access |
| --- | --- |
| `System Manager` | Full access to all fields, including permlevel-1 (ID image/number/raw OCR text). |
| `Visitor Verifier` | Read/write on Visitor/Card/Log including permlevel-1 fields; can call `mark_verified`. Intended for reception/security staff who handle ID scans. |
| `Employee` | Read/write/create on Visitor/Card/Log at the default permlevel (name, purpose, host, status) but **not** the ID image, ID number, or raw OCR text, and **not** delete. |

`ocr_verified`, `verified_by`, `verified_on` are read-only at the doctype level for every role — the only way to set them is the `Visitor.mark_verified()` method, which itself checks for `System Manager`/`Visitor Verifier`. `Visitors Registration Card.status`/`current_visitor` are permlevel-1, write-restricted to `System Manager` (for manual Lost/Damaged/Disabled marking) — normal scans mutate them via `ignore_permissions=True` server-side code, not direct field edits.

## Reports and Dashboards

| Report | Type | Description |
| --- | --- | --- |
| Current Visitors In Premises | Query Report | Visitors with an `Assigned` badge right now. |
| Daily Visitor Log | Query Report | All log entries in a date range. |
| Unreturned Badge Report | Query Report | Badges still `Assigned`, with hours-on-site. |
| Visitor by Host Employee | Script Report | Visit counts and last-visit date grouped by host. |
| OCR Exception Report | Script Report | Visitors with failed OCR extraction, low confidence, or pending verification. |
| Visitor Audit Trail | Script Report | Field-level change history (who scanned, who verified, when) — built on Frappe's own Version tracking, no extra bookkeeping. |

All six are linked from the "Visitors" workspace, plus the pre-existing number cards/chart (Active Visitors On-Premise, Total Visits Today, Unique Visitors This Month, Active Staff Hosts Today, Monthly Visitor Traffic).

## APIs

### Badge state machine — `visitor/api/badge.py`

| Method | Purpose | Key Parameters |
| --- | --- | --- |
| `assign_badge` | Link an available badge to an ID-verified visitor. | `visitor`, `qr_code` |
| `scan_badge` | Gate scan: first scan checks IN, next scan of the same badge checks OUT and releases it. | `qr_code`, `gate_location` |

### OCR — `visitor/api/ocr.py`

| Method | Purpose | Key Parameters |
| --- | --- | --- |
| `extract_id_details` | Read an uploaded (private) ID image and return best-effort structured fields. Read-only — never saves to a Visitor record. | `file_url`, `id_type` |

### Doc method — `Visitor.mark_verified()`

Confirms a human has reviewed the OCR-extracted ID; the only path that sets `ocr_verified`/`verified_by`/`verified_on`. Callable via `frm.call("mark_verified")` or `POST /api/v2/document/Visitor/<name>/method/mark_verified`.

### Legacy — `visitor/api/visitor_scan.py`

Kept for backward compatibility with existing scanner/kiosk/mobile integrations; internally delegates to `badge.py`.

| Method | Purpose | Key Parameters |
| --- | --- | --- |
| `visitors_scan` | `api_type=scan` delegates to `scan_badge`; `api_type=register` reports badge availability; `api_type=search` re-checks-in a known visitor by a prior log name. | `qr_code`, `api_type`, `log_name` |
| `create_visitor_log` | Quick check-in for a **returning, already-verified** visitor by phone number. Does not create new Visitor records — first-time visitors must be registered and verified via the Desk form. | `qr_code`, `contact_number`, `gate_location` |
| `get_visitor_status` | Reports whether a badge exists, and who (if anyone) currently holds it. | `qr_code` |
| `register_visitor` | Creates a `Visitor` record (e.g. from a mobile pre-registration app); does not check anyone in. | `first_name`, `last_name`, `email_address`, `phone_number`, `company_organization`, `purpose`, `host_employee`, `expected_duration`, `visitor_image` |
| `get_employees` | Returns active employees, or a system-user fallback. | none |
| `get_visitor_logs` | Returns recent visitor logs with optional filtering. | `limit`, `log_type`, `date_from`, `date_to` |

## Hooks and Events

- `doc_events`: `Visitors Registration Log.before_insert` → `sync_visitor_profile` (auto-creates/links a `Visitor` record from `contact_number` if one doesn't already exist).
- No scheduled jobs.
- `visitor.js` (doctype-scoped client script, auto-loaded by Frappe — no `hooks.py` wiring needed) adds the **Scan ID** and **Verify ID** buttons to the `Visitor` form.

## Developer Setup

```bash
cd $PATH_TO_YOUR_BENCH/apps/visitor
pre-commit install
bench --site your-site-name migrate
bench --site your-site-name clear-cache
```

## Testing

```bash
bench --site your-test-site set-config allow_tests true
bench --site your-test-site run-tests --app visitor --skip-test-records
```

`--skip-test-records` avoids Frappe's automatic test-record generation for linked doctypes (`Employee` → `Cost Center` on some ERPNext setups can fail here for reasons unrelated to this app — see `visitor/tests/test_utils.py` for the workaround used in this app's own test factories). Run tests on a dedicated test site, not your working/demo site.

## Project Structure

```text
visitor/
  api/
    badge.py              # assign_badge / scan_badge state machine
    ocr.py                 # extract_id_details
    visitor_scan.py         # legacy scan/registration endpoints (delegates to badge.py)
  ocr_backends/
    base.py
    tesseract_backend.py
    paddleocr_backend.py
    id_parsers.py
  patches/
    v1_0/
  tests/
    test_badge_scan.py
    test_ocr.py
    test_utils.py
  visitor/
    doctype/
      visitor/                          # Visitor.js (Scan ID / Verify ID buttons)
      visitors_registration_card/
      visitors_registration_log/
      visitor_settings/
    report/
      current_visitors_in_premises/
      daily_visitor_log/
      unreturned_badge_report/
      visitor_by_host_employee/
      ocr_exception_report/
      visitor_audit_trail/
    workspace/visitors/
  hooks.py
  modules.txt
  patches.txt
```

## Migration Notes

`visitor/patches.txt` includes post-model-sync patches that: (1) create the `Visitor Verifier` role, and (2) add the six new reports to the existing "Visitors" workspace (workspace content isn't overwritten by a plain `bench migrate` once it exists in the DB, so this is applied explicitly via patch).

## Upgrade Guide

```bash
cd $PATH_TO_YOUR_BENCH/apps/visitor
git pull
cd $PATH_TO_YOUR_BENCH
bench --site your-site-name migrate
bench --site your-site-name clear-cache
```

Before upgrading production, test the full register → scan → verify → assign → scan IN → scan OUT flow on a staging site.

## Uninstallation

```bash
bench --site your-site-name uninstall-app visitor
```

Back up visitor records first — no custom uninstall hooks exist to preserve data.

## Troubleshooting

| Symptom | What to Check |
| --- | --- |
| "Visitor ID must be verified before check-in" | The visitor hasn't been through Scan ID + Verify ID yet — this is enforced server-side, not just in the UI. |
| "PaddleOCR is not installed on this server" | Install it with `pip install "visitor[paddleocr]"`, or switch `Visitor Settings.ocr_backend` back to Tesseract. |
| OCR returns empty/garbled text | Check the `tesseract-ocr` system package is installed (`tesseract --version`); check image quality/lighting. |
| "Badge is not available" | The badge is already `Assigned` to someone else, or marked `Lost`/`Damaged`/`Disabled` — check `Visitors Registration Card.status`. |
| Host employee cannot be selected | Confirm the `Employee` DocType exists and has active records. |
| `create_visitor_log` fails for a walk-in visitor | Expected — that endpoint only re-checks-in an already-verified returning visitor. New visitors must be registered and verified via the Desk form first. |

## Security

- Scanned ID images are forced private server-side in `extract_id_details`, regardless of how the client uploaded them.
- `id_number`, `scanned_id_image`, `ocr_raw_text`, `ocr_suggested_json` are permlevel-1 — restrict `Visitor Verifier` assignment to staff who actually need to see ID data.
- `ocr_verified` can only change via `Visitor.mark_verified()`, which enforces its own role check independent of the client UI.
- Several legacy API write paths use `ignore_permissions=True` for kiosk/mobile use — protect these endpoints with authentication appropriate to your deployment.
- Define a retention/purge policy for visitor contact details and ID images — not built in.
- Use HTTPS for API clients.

## Support and Maintenance

| Field | Value |
| --- | --- |
| Publisher | Aakvatech |
| Email | `info@aakvatech.com` |

## License

MIT. See [license.txt](license.txt).

## Maintainers

- Aakvatech
- `info@aakvatech.com`
