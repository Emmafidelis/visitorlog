import json

import frappe

REPORT_LABELS = [
	"Current Visitors In Premises",
	"Daily Visitor Log",
	"Unreturned Badge Report",
	"Visitor by Host Employee",
	"OCR Exception Report",
	"Visitor Audit Trail",
]


def execute():
	"""Add the 6 new reports to the existing 'Visitors' workspace.

	bench migrate does not overwrite an existing Workspace document's content
	from its JSON fixture (so in-app customizations survive upgrades), so the
	new report links have to be added here explicitly instead.
	"""
	if not frappe.db.exists("Workspace", "Visitors"):
		return

	workspace = frappe.get_doc("Workspace", "Visitors")

	if any(link.label == "Reports" for link in workspace.links):
		return

	workspace.append(
		"links",
		{
			"label": "Reports",
			"type": "Card Break",
			"link_type": "DocType",
			"link_count": len(REPORT_LABELS),
		},
	)
	for label in REPORT_LABELS:
		workspace.append(
			"links",
			{
				"label": label,
				"type": "Link",
				"link_type": "Report",
				"link_to": label,
				"is_query_report": 1,
			},
		)

	content = json.loads(workspace.content or "[]")
	content.append({"type": "card", "data": {"card_name": "Reports", "col": 4}})
	workspace.content = json.dumps(content)

	workspace.save(ignore_permissions=True)
