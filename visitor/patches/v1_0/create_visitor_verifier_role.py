import frappe


def execute():
	"""Create the 'Visitor Verifier' role used to gate OCR ID verification."""
	if not frappe.db.exists("Role", "Visitor Verifier"):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": "Visitor Verifier",
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)
