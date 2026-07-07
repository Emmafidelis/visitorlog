class OCRBackend:
	"""Interface every OCR backend implements.

	Deliberately framework-agnostic (no frappe imports) so backends can be
	unit-tested and mocked without a Frappe site.
	"""

	def extract(self, image_path: str) -> dict:
		"""Read text from the image at image_path.

		Returns {"raw_text": str, "confidence": float} where confidence is 0-100.
		"""
		raise NotImplementedError
