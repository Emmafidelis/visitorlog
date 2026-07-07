import frappe


def get_test_host_employee():
	"""Minimal Employee for use as a Visitor's host_employee.

	Deliberately does not use ERPNext's own make_employee() test helper: on
	this bench it pulls in a Cost Center autoname fixture chain that expects
	a "_Test Company" record which doesn't exist on this site (only the real
	company "Seven Safaris" does), and fails with an unrelated TypeError.
	"""
	existing = frappe.db.get_value("Employee", {"employee_name": "Visitor App Test Host"}, "name")
	if existing:
		return existing

	employee = frappe.get_doc(
		{
			"doctype": "Employee",
			"employee_name": "Visitor App Test Host",
			"first_name": "Visitor App Test Host",
			"company": frappe.db.get_value("Company", {}, "name"),
		}
	)
	employee.insert(ignore_permissions=True, ignore_mandatory=True)
	return employee.name


def make_test_visitor(host_employee, ocr_verified=0, **kwargs):
	visitor = frappe.get_doc(
		{
			"doctype": "Visitor",
			"first_name": kwargs.get("first_name", "Test"),
			"last_name": kwargs.get("last_name", "Visitor"),
			"email_address": kwargs.get("email_address", frappe.generate_hash(length=8) + "@example.com"),
			"phone_number": kwargs.get("phone_number", "0700" + frappe.generate_hash(length=6)[:6]),
			"purpose": kwargs.get("purpose", "Testing"),
			"host_employee": host_employee,
		}
	)
	visitor.insert(ignore_permissions=True)
	if ocr_verified:
		visitor.db_set("scanned_id_image", "/private/files/test.jpg")
		visitor.db_set("ocr_raw_text", "TEST ID TEXT")
		visitor.reload()
		visitor.mark_verified()
	return visitor
