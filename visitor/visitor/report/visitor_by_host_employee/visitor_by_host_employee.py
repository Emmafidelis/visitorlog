# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Max
from pypika import Order


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Host Employee"), "fieldname": "host_employee", "fieldtype": "Link", "options": "Employee", "width": 150},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Total Visits"), "fieldname": "total_visits", "fieldtype": "Int", "width": 110},
		{"label": _("Last Visit Date"), "fieldname": "last_visit", "fieldtype": "Date", "width": 130},
	]


def get_data(filters):
	visitor = DocType("Visitor")
	employee = DocType("Employee")

	query = (
		frappe.qb.from_(visitor)
		.left_join(employee)
		.on(employee.name == visitor.host_employee)
		.select(
			visitor.host_employee,
			employee.employee_name,
			Count(visitor.name).as_("total_visits"),
			Max(visitor.visit_date).as_("last_visit"),
		)
		.where(visitor.host_employee.isnotnull())
		.groupby(visitor.host_employee)
		.orderby(Count(visitor.name), order=Order.desc)
	)

	if filters.get("host_employee"):
		query = query.where(visitor.host_employee == filters["host_employee"])
	if filters.get("from_date"):
		query = query.where(visitor.visit_date >= filters["from_date"])
	if filters.get("to_date"):
		query = query.where(visitor.visit_date <= filters["to_date"])

	return query.run(as_dict=True)
