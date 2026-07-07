# Copyright (c) 2026, Aakvatech and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from visitor.tests.test_utils import get_test_host_employee, make_test_visitor


class TestVisitor(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.host_employee = get_test_host_employee()

	def test_full_name_is_derived(self):
		visitor = make_test_visitor(self.host_employee, first_name="Amina", last_name="Hassan")
		self.assertEqual(visitor.full_name, "Amina Hassan")

	def test_checked_in_blocked_without_ocr_verification(self):
		visitor = make_test_visitor(self.host_employee)
		self.assertFalse(visitor.ocr_verified)
		visitor.status = "Checked In"
		self.assertRaises(frappe.ValidationError, visitor.save)

	def test_mark_verified_requires_a_scan(self):
		visitor = make_test_visitor(self.host_employee)
		self.assertRaises(frappe.ValidationError, visitor.mark_verified)

	def test_mark_verified_sets_audit_fields(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		self.assertTrue(visitor.ocr_verified)
		self.assertEqual(visitor.verified_by, frappe.session.user)
		self.assertIsNotNone(visitor.verified_on)

	def test_checked_in_allowed_after_verification(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		visitor.status = "Checked In"
		visitor.save()
		self.assertEqual(visitor.status, "Checked In")
		self.assertIsNotNone(visitor.check_in_time)
