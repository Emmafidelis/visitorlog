# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _

TRACKED_DOCTYPES = ["Visitor", "Visitors Registration Card", "Visitors Registration Log"]
IGNORED_FIELDS = {"modified"}


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Timestamp"), "fieldname": "timestamp", "fieldtype": "Datetime", "width": 160},
		{"label": _("Document Type"), "fieldname": "ref_doctype", "fieldtype": "Data", "width": 170},
		{"label": _("Document"), "fieldname": "docname", "fieldtype": "Dynamic Link", "options": "ref_doctype", "width": 150},
		{"label": _("Changed By"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Change"), "fieldname": "change", "fieldtype": "Data", "width": 360},
	]


def get_data(filters):
	# Reuses Frappe's built-in Version doctype — all three doctypes already have
	# track_changes=1, so field-level history is already being captured for free.
	# Date range is pushed into the query itself (not filtered in Python after
	# the fact) so a busy site doesn't have to load its entire Version history
	# into memory just to show "today".
	version_filters = {"ref_doctype": ["in", TRACKED_DOCTYPES]}
	if filters.get("from_date"):
		version_filters["creation"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		to_date_end = f"{filters['to_date']} 23:59:59"
		if "creation" in version_filters:
			version_filters["creation"] = ["between", [filters["from_date"], to_date_end]]
		else:
			version_filters["creation"] = ["<=", to_date_end]

	versions = frappe.get_all(
		"Version",
		filters=version_filters,
		fields=["ref_doctype", "docname", "owner", "creation", "data"],
		order_by="creation desc",
		limit_page_length=0,
	)

	rows = []
	for version in versions:
		try:
			data = json.loads(version.data or "{}")
		except ValueError:
			continue

		for field, old_value, new_value in data.get("changed") or []:
			if field in IGNORED_FIELDS:
				continue
			rows.append(
				{
					"timestamp": version.creation,
					"ref_doctype": version.ref_doctype,
					"docname": version.docname,
					"user": version.owner,
					"change": _("{0}: {1} → {2}").format(field, old_value, new_value),
				}
			)

	return rows
