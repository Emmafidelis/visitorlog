# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VisitorsRegistrationCard(Document):
	def validate(self):
		# A card can only be linked to a visitor while it is actually Assigned.
		# Covers a System Manager manually marking a badge Lost/Damaged/Disabled
		# from the Desk form (the scan flow already clears this itself).
		if self.status != "Assigned" and self.current_visitor:
			self.current_visitor = None

		# The reverse must also hold: "Assigned" with no visitor is an invalid
		# state that would later crash the gate scan (badge.py looks up
		# frappe.get_doc("Visitor", card.current_visitor) assuming it's set).
		if self.status == "Assigned" and not self.current_visitor:
			frappe.throw(frappe._("An Assigned badge must have a Current Visitor."))

		# Mandatory-verification-before-badge is enforced here too (not just in
		# visitor.api.badge.assign_badge) so a direct Desk edit of this form
		# can't hand out a badge to an unverified visitor as a side door.
		if self.status == "Assigned" and self.current_visitor:
			if not frappe.db.get_value("Visitor", self.current_visitor, "ocr_verified"):
				frappe.throw(frappe._("{0}'s ID must be verified before a badge can be assigned.").format(self.current_visitor))
