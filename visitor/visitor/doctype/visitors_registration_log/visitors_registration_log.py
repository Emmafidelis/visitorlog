# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VisitorsRegistrationLog(Document):
	def before_save(self):
		"""Set time_in when log_type is IN and time_out when log_type is OUT"""
		if self.log_type == "IN" and not self.time_in:
			self.time_in = frappe.utils.now()
		elif self.log_type == "OUT" and not self.time_out:
			self.time_out = frappe.utils.now()
