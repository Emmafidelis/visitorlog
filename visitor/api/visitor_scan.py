# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
import json


@frappe.whitelist()
def visitors_scan():
    """
    API endpoint for visitor scanning functionality

    Parameters:
    - qr_code: QR code from the visitor card
    - api_type: Type of API call (scan, register, search)
    - log_name: Name of the log entry (for search type)

    Returns various status messages based on the operation
    """
    qr_code = frappe.form_dict.get("qr_code")
    api_type = frappe.form_dict.get("api_type")
    log_name = frappe.form_dict.get("log_name")

    # Check if the card exists
    card = frappe.db.get_list(
        "Visitors Registration Card",
        filters={
            "name": qr_code,
        },
    )

    if card:
        # Check for existing IN log with this QR code
        log = frappe.db.get_list(
            "Visitors Registration Log",
            filters={"log_type": "IN", "qr_code": qr_code},
            fields=["log_type", "qr_code", "name"],
        )

        if api_type == "scan":
            if log:
                # Sign out the visitor
                frappe.db.set_value(
                    "Visitors Registration Log", log[0].name, "log_type", "OUT"
                )
                frappe.db.set_value(
                    "Visitors Registration Log",
                    log[0].name,
                    "time_out",
                    frappe.utils.now(),
                )
                frappe.db.commit()
                frappe.response["message"] = {"status": "card_signed_out"}
            else:
                frappe.response["message"] = {"status": "card_not_in_use"}

        elif api_type == "register":
            if log:
                frappe.response["message"] = {"status": "card_in_use"}
            else:
                frappe.response["message"] = {"status": "card_to_created"}

        elif api_type == "search":
            if log:
                frappe.response["message"] = {"status": "card_in_use"}
            else:
                if log_name:
                    doc = frappe.get_doc("Visitors Registration Log", log_name)
                    if doc.log_type == "IN":
                        frappe.response["message"] = {"status": "visitor_is_in"}
                    else:
                        doc.log_type = "IN"
                        doc.qr_code = qr_code
                        doc.time_in = frappe.utils.now()
                        doc.save(ignore_permissions=True)
                        frappe.response["message"] = {"status": "card_signed_in"}
                else:
                    frappe.response["message"] = {"status": "log_name_required"}

        else:
            frappe.response["message"] = {"status": "set_api_type"}

    else:
        frappe.response["message"] = {"status": "card_not_existing"}


@frappe.whitelist()
def create_visitor_log():
    """
    API endpoint to create a new visitor registration log

    Parameters:
    - full_name: Visitor's full name
    - contact_number: Visitor's contact number
    - address: Visitor's address
    - purpose: Purpose of visit
    - employee: Employee being visited
    - qr_code: QR code of the card
    - visitor_image: Base64 encoded image (optional)

    Returns success/error status
    """
    try:
        data = frappe.form_dict

        # Create new visitor log
        log = frappe.get_doc(
            {
                "doctype": "Visitors Registration Log",
                "full_name": data.get("full_name"),
                "contact_number": data.get("contact_number"),
                "address": data.get("address"),
                "purpose": data.get("purpose"),
                "employee": data.get("employee"),
                "log_type": "IN",
                "qr_code": data.get("qr_code"),
                "time_in": frappe.utils.now(),
            }
        )

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["message"] = {
            "status": "success",
            "log_name": log.name,
            "message": "Visitor registered successfully",
        }

    except Exception as e:
        frappe.log_error(
            f"Error creating visitor log: {str(e)}", "Visitor Registration Error"
        )
        frappe.response["message"] = {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_visitor_status():
    """
    API endpoint to get current status of a visitor by QR code

    Parameters:
    - qr_code: QR code to check

    Returns visitor status information
    """
    qr_code = frappe.form_dict.get("qr_code")

    if not qr_code:
        frappe.response["message"] = {
            "status": "error",
            "message": "QR code is required",
        }
        return

    # Check if card exists
    card = frappe.db.get_list(
        "Visitors Registration Card",
        filters={"name": qr_code},
        fields=["name", "label"],
    )

    if not card:
        frappe.response["message"] = {"status": "card_not_existing"}
        return

    # Get current visitor log
    current_log = frappe.db.get_list(
        "Visitors Registration Log",
        filters={"qr_code": qr_code, "log_type": "IN"},
        fields=["name", "full_name", "time_in", "purpose", "employee"],
        order_by="creation desc",
        limit=1,
    )

    if current_log:
        frappe.response["message"] = {
            "status": "visitor_in",
            "card_info": card[0],
            "visitor_info": current_log[0],
        }
    else:
        frappe.response["message"] = {"status": "card_available", "card_info": card[0]}


@frappe.whitelist()
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
                    "is_private": 0,
                }
            )
            file_doc.insert()
            visitor.visitor_image = file_doc.file_url

        visitor.insert(ignore_permissions=True)
        frappe.db.commit()

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





@frappe.whitelist()
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


@frappe.whitelist()
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
