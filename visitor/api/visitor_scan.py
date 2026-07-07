# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from visitor.api.badge import assign_badge, scan_badge


@frappe.whitelist(methods=["POST"])
def visitors_scan(qr_code: str, api_type: str, log_name: str | None = None):
	"""Legacy scan endpoint, kept for existing scanner/kiosk integrations.

	- api_type="scan": gate scan — toggles the badge IN then OUT.
	  See visitor.api.badge.scan_badge for the state machine.
	- api_type="register": reports whether a badge is currently available.
	- api_type="search": re-check-in a previously registered, already
	  ID-verified visitor by referencing one of their earlier log entries.
	"""
	if not frappe.db.exists("Visitors Registration Card", qr_code):
		frappe.response["message"] = {"status": "card_not_existing"}
		return

	if api_type == "scan":
		try:
			frappe.response["message"] = scan_badge(qr_code=qr_code)
		except frappe.ValidationError as e:
			frappe.clear_messages()
			frappe.response["message"] = {"status": "error", "message": str(e)}

	elif api_type == "register":
		# Only a truly Available badge is safe to hand out — Lost/Damaged/Disabled
		# must report as unusable too, not just "Assigned".
		status = frappe.db.get_value("Visitors Registration Card", qr_code, "status")
		frappe.response["message"] = {"status": "card_to_created" if status == "Available" else "card_in_use"}

	elif api_type == "search":
		if not log_name:
			frappe.response["message"] = {"status": "log_name_required"}
			return

		log = frappe.get_doc("Visitors Registration Log", log_name)
		if log.log_type == "IN":
			frappe.response["message"] = {"status": "visitor_is_in"}
			return

		if not log.visitor:
			frappe.response["message"] = {
				"status": "error",
				"message": "This log has no linked visitor profile; re-check-in isn't possible.",
			}
			return

		try:
			assign_badge(visitor=log.visitor, qr_code=qr_code)
			frappe.response["message"] = scan_badge(qr_code=qr_code)
		except frappe.ValidationError as e:
			frappe.clear_messages()
			frappe.response["message"] = {"status": "error", "message": str(e)}

	else:
		frappe.response["message"] = {"status": "set_api_type"}


@frappe.whitelist(methods=["POST"])
def create_visitor_log(qr_code: str, contact_number: str | None = None, gate_location: str | None = None):
	"""Quick check-in for a returning visitor whose ID was already verified on
	a previous visit — looked up by phone number.

	This endpoint deliberately does NOT create new Visitor records: a
	first-time visitor must be registered and have their ID verified at
	reception (see the Visitor form / Scan ID flow) before they can be
	checked in, in line with the mandatory human-verification requirement.

	contact_number is optional in the signature (rather than required) so a
	caller omitting it gets this function's own JSON error response instead
	of Frappe's raw "missing required argument" error before the try/except
	below even runs.
	"""
	try:
		if not contact_number:
			frappe.throw(_("A contact number is required to look up a returning visitor."))

		visitor_name = frappe.db.get_value("Visitor", {"phone_number": contact_number}, "name")
		if not visitor_name:
			frappe.throw(
				_("No verified visitor profile found for {0}. Please register and verify ID at reception.").format(
					contact_number
				)
			)

		assign_badge(visitor=visitor_name, qr_code=qr_code)
		result = scan_badge(qr_code=qr_code, gate_location=gate_location)

		frappe.response["message"] = {
			"status": "success",
			"log_name": result.get("log"),
			"message": "Visitor checked in successfully",
		}

	except Exception as e:
		frappe.clear_messages()
		frappe.log_error(f"Error creating visitor log: {str(e)}", "Visitor Registration Error")
		frappe.response["message"] = {"status": "error", "message": str(e)}


@frappe.whitelist(methods=["GET"])
def get_visitor_status(qr_code: str):
	"""API endpoint to get current status of a badge, and who (if anyone) holds it."""
	card = frappe.db.get_value(
		"Visitors Registration Card",
		qr_code,
		["name", "label", "status", "current_visitor"],
		as_dict=True,
	)

	if not card:
		frappe.response["message"] = {"status": "card_not_existing"}
		return

	if card.status == "Assigned" and card.current_visitor:
		visitor_info = frappe.db.get_value(
			"Visitor",
			card.current_visitor,
			["name", "full_name", "check_in_time", "purpose", "host_employee"],
			as_dict=True,
		)
		frappe.response["message"] = {"status": "visitor_in", "card_info": card, "visitor_info": visitor_info}
	else:
		frappe.response["message"] = {"status": "card_available", "card_info": card}


@frappe.whitelist(methods=["POST"])
def register_visitor():
	"""
	API endpoint for registering a new visitor from Flutter app

	Parameters:
	- first_name: Visitor's first name
	- last_name: Visitor's last name
	- email_address: Visitor's email
	- phone_number: Visitor's phone number
	- company_organization: Visitor's company/organization
	- purpose: Purpose of visit
	- host_employee: Host employee ID
	- expected_duration: Expected duration of visit
	- visitor_image: Base64 encoded image (optional)

	Returns visitor registration details
	"""
	try:
		data = frappe.form_dict

		# Create new visitor record
		visitor = frappe.get_doc(
			{
				"doctype": "Visitor",
				"first_name": data.get("first_name"),
				"last_name": data.get("last_name"),
				"email_address": data.get("email_address"),
				"phone_number": data.get("phone_number"),
				"company_organization": data.get("company_organization"),
				"purpose": data.get("purpose"),
				"host_employee": data.get("host_employee"),
				"expected_duration": data.get("expected_duration"),
				"visit_date": frappe.utils.today(),
				"status": "Registered",
			}
		)

		# Handle visitor image if provided
		if data.get("visitor_image"):
			# Save the image file
			file_doc = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": f"visitor_{visitor.name}_photo.jpg",
					"content": data.get("visitor_image"),
					"decode": True,
					"is_private": 1,
				}
			)
			file_doc.insert()
			visitor.visitor_image = file_doc.file_url

		visitor.insert(ignore_permissions=True)

		frappe.response["message"] = {
			"status": "success",
			"visitor_id": visitor.name,
			"full_name": visitor.full_name,
			"message": "Visitor registered successfully",
			"badge_info": {
				"visitor_name": visitor.full_name,
				"company": visitor.company_organization,
				"host": visitor.host_employee,
				"date": visitor.visit_date,
				"purpose": visitor.purpose,
			},
		}

	except Exception as e:
		frappe.log_error(f"Visitor registration error: {str(e)}")
		frappe.response["message"] = {
			"status": "error",
			"message": f"Registration failed: {str(e)}",
		}


@frappe.whitelist(methods=["GET"])
def get_employees():
	"""
	API endpoint to get list of employees for host selection

	Returns list of employees with basic information
	"""
	try:
		if frappe.db.exists("DocType", "Employee"):
			# Get employees from ERPNext Employee doctype
			employees = frappe.db.get_list(
				"Employee",
				filters={"status": "Active"},
				fields=[
					"name",
					"employee_name",
					"department",
					"designation",
					"company_email",
				],
				limit=100,
				order_by="employee_name",
			)

			frappe.response["message"] = {
				"status": "success",
				"data": employees,
				"count": len(employees),
			}
		else:
			# Fallback: get users with Employee role
			users = frappe.db.get_list(
				"User",
				filters={"enabled": 1, "user_type": "System User"},
				fields=["name", "full_name", "email"],
				limit=100,
				order_by="full_name",
			)

			# Format as employee-like structure
			employee_data = []
			for user in users:
				employee_data.append(
					{
						"name": user.name,
						"employee_name": user.full_name or user.name,
						"department": "General",
						"designation": "Employee",
						"company_email": user.email,
					}
				)

			frappe.response["message"] = {
				"status": "success",
				"data": employee_data,
				"count": len(employee_data),
			}

	except Exception as e:
		frappe.log_error(f"Error fetching employees: {str(e)}", "Employee Fetch Error")
		frappe.response["message"] = {
			"status": "error",
			"message": f"Failed to fetch employees: {str(e)}",
		}


@frappe.whitelist(methods=["GET"])
def get_visitor_logs():
	"""
	API endpoint to get visitor logs with optional filtering

	Parameters:
	- limit: Number of records to return (default: 20)
	- log_type: Filter by log type (IN/OUT)
	- date_from: Filter from date (YYYY-MM-DD)
	- date_to: Filter to date (YYYY-MM-DD)

	Returns list of visitor logs
	"""
	try:
		data = frappe.form_dict
		limit = int(data.get("limit", 20))
		log_type = data.get("log_type")
		date_from = data.get("date_from")
		date_to = data.get("date_to")

		filters = {}
		if log_type:
			filters["log_type"] = log_type
		if date_from:
			filters["creation"] = [">=", date_from]
		if date_to:
			if "creation" in filters:
				filters["creation"] = ["between", [date_from, date_to]]
			else:
				filters["creation"] = ["<=", date_to]

		logs = frappe.db.get_list(
			"Visitors Registration Log",
			filters=filters,
			fields=[
				"name",
				"full_name",
				"contact_number",
				"purpose",
				"employee",
				"log_type",
				"time_in",
				"time_out",
				"qr_code",
			],
			order_by="creation desc",
			limit=limit,
		)

		frappe.response["message"] = {
			"status": "success",
			"data": logs,
			"count": len(logs),
		}

	except Exception as e:
		frappe.log_error(f"Error getting visitor logs: {str(e)}", "Visitor Logs Error")
		frappe.response["message"] = {"status": "error", "message": str(e)}


def sync_visitor_profile(doc, method=None):
	"""
	Document Hook: Runs before inserting a new Visitors Registration Log.
	Ensures that a master Visitor record exists for the given contact_number,
	and links it via the `visitor` field if that wasn't already set by the caller.
	"""
	if doc.log_type != "IN":
		return

	contact_number = doc.contact_number
	full_name = doc.full_name or "Unknown Visitor"

	if not contact_number:
		return

	existing = frappe.db.get_value("Visitor", {"phone_number": contact_number}, "name")
	if existing:
		if not doc.visitor:
			doc.visitor = existing
		return

	name_parts = full_name.split(" ", 1)
	first_name = name_parts[0]
	last_name = name_parts[1] if len(name_parts) > 1 else "-"

	visitor = frappe.get_doc(
		{
			"doctype": "Visitor",
			"first_name": first_name,
			"last_name": last_name,
			"phone_number": contact_number,
			"email_address": f"{contact_number}@visitor.local",
			"purpose": doc.purpose,
			"host_employee": doc.employee,
			"visit_date": frappe.utils.today(),
			"status": "Registered",
		}
	)
	# If there's an image attached to the log, attach it to the visitor
	if doc.visitor_image:
		visitor.visitor_image = doc.visitor_image

	visitor.flags.ignore_mandatory = True
	visitor.flags.ignore_validate = True

	try:
		visitor.insert(ignore_permissions=True)
		if not doc.visitor:
			doc.visitor = visitor.name
	except Exception as e:
		if "phone" in str(e).lower():
			frappe.clear_messages()
			visitor.phone_number = None
			try:
				visitor.insert(ignore_permissions=True)
				if not doc.visitor:
					doc.visitor = visitor.name
			except Exception as inner_e:
				frappe.log_error(
					f"Failed to auto-create visitor profile after fallback: {str(inner_e)[:100]}",
					"Visitor Sync Error",
				)
		else:
			frappe.log_error(f"Failed to auto-create visitor profile: {str(e)[:100]}", "Visitor Sync Error")
