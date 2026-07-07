# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	return get_columns(), get_data()


def get_columns():
	return [
		{"label": _("Visitor"), "fieldname": "name", "fieldtype": "Link", "options": "Visitor", "width": 120},
		{"label": _("Full Name"), "fieldname": "full_name", "fieldtype": "Data", "width": 160},
		{"label": _("ID Type"), "fieldname": "id_type", "fieldtype": "Data", "width": 120},
		{"label": _("OCR Confidence"), "fieldname": "ocr_confidence", "fieldtype": "Percent", "width": 120},
		{"label": _("OCR Verified"), "fieldname": "ocr_verified", "fieldtype": "Check", "width": 100},
		{"label": _("Exception Reason"), "fieldname": "reason", "fieldtype": "Data", "width": 220},
	]


def get_data():
	# get_cached_doc (not get_single_value) so the DocField default applies
	# even before Visitor Settings has ever been saved via the Desk UI.
	threshold = frappe.get_cached_doc("Visitor Settings").ocr_confidence_threshold
	fields = ["name", "full_name", "id_type", "ocr_confidence", "ocr_verified"]
	rows = {}

	def add_reason(records, reason):
		for record in records:
			rows.setdefault(record.name, {**record, "reason": ""})
			existing = rows[record.name]["reason"]
			rows[record.name]["reason"] = f"{existing}; {reason}" if existing else reason

	add_reason(
		frappe.get_all(
			"Visitor",
			filters={"scanned_id_image": ["is", "set"], "ocr_raw_text": ["is", "not set"]},
			fields=fields,
		),
		_("OCR extraction failed"),
	)
	add_reason(
		frappe.get_all(
			"Visitor",
			filters={"scanned_id_image": ["is", "set"], "ocr_confidence": ["<", threshold]},
			fields=fields,
		),
		_("Low OCR confidence (below {0}%)").format(threshold),
	)
	add_reason(
		frappe.get_all(
			"Visitor",
			filters={"scanned_id_image": ["is", "set"], "ocr_verified": 0},
			fields=fields,
		),
		_("Not yet verified"),
	)

	return sorted(rows.values(), key=lambda r: r["name"])
