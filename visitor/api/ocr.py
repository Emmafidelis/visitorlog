# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe

from visitor.ocr_backends.id_parsers import parse_id_fields


def _get_backend():
	# get_cached_doc (not get_single_value) so the DocField default applies
	# even before Visitor Settings has ever been saved via the Desk UI.
	settings = frappe.get_cached_doc("Visitor Settings")

	if settings.ocr_backend == "PaddleOCR (Local)":
		from visitor.ocr_backends.paddleocr_backend import PaddleOCRBackend

		return PaddleOCRBackend()

	from visitor.ocr_backends.tesseract_backend import TesseractBackend

	return TesseractBackend()


@frappe.whitelist(methods=["POST"])
def extract_id_details(file_url: str, id_type: str | None = None) -> dict:
	"""Read a scanned ID image and return best-effort structured fields.

	This is read/compute-only: it never writes to a Visitor record. The
	caller (the Visitor form's Scan ID button) populates an unsaved form with
	the result, the human reviews/corrects every field, and only the normal
	Save persists anything — satisfying the "OCR assists, human verifies"
	requirement structurally rather than by convention.
	"""
	# file_url isn't guaranteed unique (Frappe can point two File docs at the
	# same physical path after content-hash dedup), so pick the most recently
	# uploaded match rather than an arbitrary one — that's always the file
	# the caller's Scan ID action just uploaded.
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name", order_by="creation desc")
	if not file_name:
		frappe.throw(frappe._("File not found: {0}").format(file_url))
	file_doc = frappe.get_doc("File", file_name)

	# ID images must never be public. This is the real enforcement point —
	# Attach/Attach Image field types don't guarantee file-level privacy on
	# their own, so re-assert it here regardless of how the file arrived.
	if not file_doc.is_private:
		file_doc.is_private = 1
		file_doc.save(ignore_permissions=True)

	try:
		result = _get_backend().extract(file_doc.get_full_path())
	except RuntimeError as e:
		frappe.throw(str(e))

	return {
		"raw_text": result["raw_text"],
		"confidence": result["confidence"],
		"fields": parse_id_fields(result["raw_text"], id_type),
	}
