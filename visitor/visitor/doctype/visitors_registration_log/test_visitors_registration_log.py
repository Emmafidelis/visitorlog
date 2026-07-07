# Copyright (c) 2026, Aakvatech and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestVisitorsRegistrationLog(FrappeTestCase):
	def test_time_in_set_automatically(self):
		log = frappe.get_doc(
			{
				"doctype": "Visitors Registration Log",
				"full_name": "Test Visitor",
				"log_type": "IN",
			}
		).insert(ignore_permissions=True)
		self.assertIsNotNone(log.time_in)
		self.assertIsNone(log.time_out)

	def test_time_out_set_automatically(self):
		log = frappe.get_doc(
			{
				"doctype": "Visitors Registration Log",
				"full_name": "Test Visitor",
				"log_type": "OUT",
			}
		).insert(ignore_permissions=True)
		self.assertIsNotNone(log.time_out)
