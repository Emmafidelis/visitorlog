# Copyright (c) 2026, Aakvatech and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from visitor.tests.test_utils import get_test_host_employee, make_test_visitor


class TestVisitorsRegistrationCard(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.host_employee = get_test_host_employee()

	def test_defaults_to_available(self):
		card = frappe.get_doc({"doctype": "Visitors Registration Card", "label": "Test Badge"}).insert(
			ignore_permissions=True
		)
		self.assertEqual(card.status, "Available")
		self.assertIsNone(card.current_visitor)

	def test_current_visitor_cleared_when_marked_lost(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		card = frappe.get_doc({"doctype": "Visitors Registration Card", "label": "Test Badge"}).insert(
			ignore_permissions=True
		)
		card.status = "Assigned"
		card.current_visitor = visitor.name
		card.save(ignore_permissions=True)

		card.status = "Lost"
		card.save(ignore_permissions=True)
		self.assertIsNone(card.current_visitor)
