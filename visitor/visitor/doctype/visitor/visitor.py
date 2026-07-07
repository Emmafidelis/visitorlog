# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Visitor(Document):
	def before_save(self):
		"""Set full name from first and last name"""
		if self.first_name and self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}"
		
		# Set check-in time when status changes to Checked In. Also refresh on
		# every fresh transition into this status (not just when blank) so a
		# returning visitor's new visit doesn't keep a stale time from a
		# previous stay.
		if self.status == "Checked In" and (not self.check_in_time or self.has_value_changed("status")):
			self.check_in_time = frappe.utils.now()

		# Same reasoning for check-out time on repeat visits.
		if self.status == "Checked Out" and (not self.check_out_time or self.has_value_changed("status")):
			self.check_out_time = frappe.utils.now()
	
	def validate(self):
		"""Validate visitor data"""
		# Ensure email is valid
		if self.email_address:
			frappe.utils.validate_email_address(self.email_address, throw=True)
		
		# Ensure phone number is provided
		if not self.phone_number:
			frappe.throw("Phone number is required")
		
		# Ensure host employee exists
		if self.host_employee:
			if not frappe.db.exists("Employee", self.host_employee):
				frappe.throw(f"Employee {self.host_employee} does not exist")

		# OCR ID must be human-verified before a visitor is allowed on premises.
		# This is the server-side enforcement of the "no check-in without verification"
		# control; the badge scan flow and the Desk UI both rely on this gate holding
		# even if called directly via the API.
		if self.status == "Checked In" and not self.ocr_verified:
			frappe.throw("Visitor ID must be verified before check-in")

	@frappe.whitelist()
	def mark_verified(self):
		"""Confirm a human has reviewed the OCR-extracted ID details.

		This is the only path that may set ocr_verified — the field itself is
		read_only so it can never be set by a plain form save.
		"""
		if not ("System Manager" in frappe.get_roles() or "Visitor Verifier" in frappe.get_roles()):
			frappe.throw("Not permitted to verify visitor ID", frappe.PermissionError)

		if not self.scanned_id_image or not self.ocr_raw_text:
			frappe.throw("Scan the visitor's ID before marking it verified")

		# save() rather than db_set(): this is the single most security-relevant
		# transition on the whole doctype, so it must go through track_changes
		# like any other edit and show up in the Visitor Audit Trail report.
		self.ocr_verified = 1
		self.verified_by = frappe.session.user
		self.verified_on = frappe.utils.now()
		self.save(ignore_permissions=True)
