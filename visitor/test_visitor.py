import frappe

def execute():
    try:
        # Create dummy employee
        emp = frappe.get_doc({
            "doctype": "Employee",
            "first_name": "Test",
            "status": "Active",
            "date_of_joining": "2020-01-01"
        })
        emp.insert(ignore_permissions=True)
    except Exception:
        emp = frappe.get_last_doc("Employee")
        
    log = frappe.get_doc({
        "doctype": "Visitors Registration Log",
        'contact_number': 'test-phone-hooks-1',
        'full_name': 'Hook User',
        'purpose': 'Testing Hook',
        'employee': emp.name if emp else '',
        'log_type': 'IN'
    })
    log.insert(ignore_permissions=True)
    
    
    error = frappe.get_last_doc("Error Log")
    if error:
        print("Last Error Log:", error.method, error.error)
