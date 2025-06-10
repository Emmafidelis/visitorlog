# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Visitor(Document):
	def before_save(self):
		"""Set full name from first and last name"""
		if self.first_name and self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}"
		
		# Set check-in time when status changes to Checked In
		if self.status == "Checked In" and not self.check_in_time:
			self.check_in_time = frappe.utils.now()
		
		# Set check-out time when status changes to Checked Out
		if self.status == "Checked Out" and not self.check_out_time:
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
