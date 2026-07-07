# Copyright (c) 2026, Aakvatech and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from visitor.api.badge import assign_badge, scan_badge
from visitor.api.visitor_scan import visitors_scan
from visitor.tests.test_utils import get_test_host_employee, make_test_visitor


def make_card():
	return frappe.get_doc({"doctype": "Visitors Registration Card", "label": "Test Badge"}).insert(
		ignore_permissions=True
	)


class TestBadgeScan(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.host_employee = get_test_host_employee()

	def test_assign_blocked_without_ocr_verification(self):
		visitor = make_test_visitor(self.host_employee)
		card = make_card()
		self.assertRaises(frappe.ValidationError, assign_badge, visitor=visitor.name, qr_code=card.name)

	def test_full_check_in_and_check_out_cycle(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		card = make_card()

		assign_badge(visitor=visitor.name, qr_code=card.name)
		card.reload()
		self.assertEqual(card.status, "Assigned")
		self.assertEqual(card.current_visitor, visitor.name)

		result_in = scan_badge(qr_code=card.name)
		self.assertEqual(result_in["status"], "checked_in")
		visitor.reload()
		self.assertEqual(visitor.status, "Checked In")

		result_out = scan_badge(qr_code=card.name)
		self.assertEqual(result_out["status"], "checked_out")
		self.assertEqual(result_in["log"], result_out["log"], "IN and OUT must close the same log row")

		card.reload()
		visitor.reload()
		self.assertEqual(card.status, "Available")
		self.assertIsNone(card.current_visitor)
		self.assertEqual(visitor.status, "Checked Out")

	def test_double_booking_is_blocked(self):
		visitor_a = make_test_visitor(self.host_employee, ocr_verified=1)
		visitor_b = make_test_visitor(self.host_employee, ocr_verified=1)
		card = make_card()

		assign_badge(visitor=visitor_a.name, qr_code=card.name)
		self.assertRaises(frappe.ValidationError, assign_badge, visitor=visitor_b.name, qr_code=card.name)

	def test_disabled_badge_cannot_be_used(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		card = make_card()
		card.status = "Disabled"
		card.save(ignore_permissions=True)

		self.assertRaises(frappe.ValidationError, scan_badge, qr_code=card.name)

	def test_orphan_exit_scan_is_blocked_by_default(self):
		card = make_card()
		self.assertRaises(frappe.ValidationError, scan_badge, qr_code=card.name)

	def test_badge_number_cleared_from_visitor_on_checkout(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		card = make_card()

		assign_badge(visitor=visitor.name, qr_code=card.name)
		visitor.reload()
		self.assertEqual(visitor.badge_number, card.name)

		scan_badge(qr_code=card.name)  # IN
		scan_badge(qr_code=card.name)  # OUT
		visitor.reload()
		self.assertIsNone(visitor.badge_number, "badge_number must not point at a badge the visitor no longer holds")

	def test_visitor_cannot_hold_two_badges_at_once(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		card_a = make_card()
		card_b = make_card()

		assign_badge(visitor=visitor.name, qr_code=card_a.name)
		self.assertRaises(frappe.ValidationError, assign_badge, visitor=visitor.name, qr_code=card_b.name)

	def test_card_cannot_be_assigned_without_a_visitor(self):
		card = make_card()
		card.status = "Assigned"
		self.assertRaises(frappe.ValidationError, card.save, ignore_permissions=True)

	def test_repeat_visit_refreshes_check_in_time(self):
		visitor = make_test_visitor(self.host_employee, ocr_verified=1)
		card = make_card()

		assign_badge(visitor=visitor.name, qr_code=card.name)
		scan_badge(qr_code=card.name)  # IN
		visitor.reload()
		first_check_in = visitor.check_in_time
		scan_badge(qr_code=card.name)  # OUT

		# ocr_verified stays true across visits, so no re-verification needed.
		assign_badge(visitor=visitor.name, qr_code=card.name)
		scan_badge(qr_code=card.name)  # IN again
		visitor.reload()
		self.assertGreater(visitor.check_in_time, first_check_in)

	def test_legacy_register_probe_rejects_disabled_badge(self):
		card = make_card()
		card.status = "Disabled"
		card.save(ignore_permissions=True)

		visitors_scan(qr_code=card.name, api_type="register")
		self.assertEqual(frappe.response["message"]["status"], "card_in_use")
