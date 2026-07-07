# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

"""Badge assignment and gate-scan state machine.

Two distinct actions, matching the physical process:
  - assign_badge: reception links an available badge to an already ID-verified
    visitor (document step 6).
  - scan_badge: the gate scan itself — first scan marks the visitor IN,
    the next scan of the same badge marks them OUT and releases it
    (document steps 7 and 9).
"""

import frappe
from frappe import _


@frappe.whitelist(methods=["POST"])
def assign_badge(visitor: str, qr_code: str) -> dict:
	"""Link an available badge to a verified visitor, ready for the gate scan."""
	card = frappe.get_doc("Visitors Registration Card", qr_code)
	if card.status != "Available":
		frappe.throw(_("Badge {0} is not available ({1}).").format(card.name, card.status))

	visitor_doc = frappe.get_doc("Visitor", visitor)
	if not visitor_doc.ocr_verified:
		frappe.throw(_("{0}'s ID must be verified before a badge can be assigned.").format(visitor_doc.full_name))

	if visitor_doc.badge_number and frappe.db.get_value(
		"Visitors Registration Card", visitor_doc.badge_number, "status"
	) == "Assigned":
		frappe.throw(
			_("{0} already holds badge {1}. Release it before assigning a new one.").format(
				visitor_doc.full_name, visitor_doc.badge_number
			)
		)

	card.status = "Assigned"
	card.current_visitor = visitor_doc.name
	card.save(ignore_permissions=True)

	visitor_doc.badge_number = card.name
	visitor_doc.save(ignore_permissions=True)

	return {"status": "assigned", "badge": card.name, "visitor": visitor_doc.name}


@frappe.whitelist(methods=["POST"])
def scan_badge(qr_code: str, gate_location: str | None = None) -> dict:
	"""Scan a badge at the gate: first scan checks the visitor IN, the next scan checks them OUT."""
	# Lock the card row for the duration of this scan so two near-simultaneous
	# scans of the same badge (double-tap, retried request) serialize instead
	# of both reading "Assigned, no open log" and both checking the visitor IN.
	frappe.db.get_value("Visitors Registration Card", qr_code, "name", for_update=True)
	card = frappe.get_doc("Visitors Registration Card", qr_code)

	if card.status in ("Lost", "Damaged", "Disabled"):
		frappe.throw(_("Badge {0} is marked {1} and cannot be used.").format(card.name, card.status))

	open_log_name = frappe.db.get_value(
		"Visitors Registration Log",
		{"qr_code": card.name, "log_type": "IN", "time_out": ["is", "not set"]},
		"name",
	)

	if card.status == "Assigned" and open_log_name:
		return _check_out(card, frappe.get_doc("Visitors Registration Log", open_log_name), gate_location)

	if card.status == "Assigned" and not open_log_name:
		return _check_in(frappe.get_doc("Visitor", card.current_visitor), card, gate_location)

	# card.status == "Available": nothing was ever assigned to open or close.
	settings = frappe.get_cached_doc("Visitor Settings")
	if settings.block_orphan_exit_scan:
		frappe.throw(_("Badge {0} is not currently assigned to any visitor.").format(card.name))

	frappe.get_doc(
		{
			"doctype": "Visitors Registration Log",
			"full_name": "Unknown Visitor",
			"log_type": "OUT",
			"qr_code": card.name,
			"time_out": frappe.utils.now(),
			"scanned_by": frappe.session.user,
			"gate_location": gate_location,
			"is_exception": 1,
			"exception_reason": "Exit scan with no matching entry record",
		}
	).insert(ignore_permissions=True)
	return {"status": "exception_logged", "badge": card.name}


def _check_in(visitor_doc, card, gate_location=None) -> dict:
	"""Shared IN transition, used by the gate scan and by the legacy quick-registration endpoint."""
	if not visitor_doc.ocr_verified:
		frappe.throw(_("{0}'s ID must be verified before check-in.").format(visitor_doc.full_name))

	log = frappe.get_doc(
		{
			"doctype": "Visitors Registration Log",
			"visitor": visitor_doc.name,
			"full_name": visitor_doc.full_name,
			"contact_number": visitor_doc.phone_number,
			"purpose": visitor_doc.purpose,
			"employee": visitor_doc.host_employee,
			"log_type": "IN",
			"qr_code": card.name,
			"time_in": frappe.utils.now(),
			"scanned_by": frappe.session.user,
			"gate_location": gate_location,
		}
	)
	log.insert(ignore_permissions=True)

	visitor_doc.status = "Checked In"
	visitor_doc.save(ignore_permissions=True)

	return {"status": "checked_in", "visitor": visitor_doc.name, "badge": card.name, "log": log.name}


def _check_out(card, log, gate_location=None) -> dict:
	"""Shared OUT transition: closes the log, releases the badge, checks the visitor out."""
	log.log_type = "OUT"
	log.time_out = frappe.utils.now()
	if gate_location:
		log.gate_location = gate_location
	log.save(ignore_permissions=True)

	card.status = "Available"
	card.current_visitor = None
	card.save(ignore_permissions=True)

	if log.visitor:
		visitor_doc = frappe.get_doc("Visitor", log.visitor)
		visitor_doc.status = "Checked Out"
		if visitor_doc.badge_number == card.name:
			visitor_doc.badge_number = None
		visitor_doc.save(ignore_permissions=True)

	return {"status": "checked_out", "visitor": log.visitor, "badge": card.name, "log": log.name}
