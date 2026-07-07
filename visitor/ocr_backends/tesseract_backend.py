import cv2
import pytesseract

from visitor.ocr_backends.base import OCRBackend


class TesseractBackend(OCRBackend):
	"""Default, lightweight OCR backend — the tesseract-ocr binary plus a
	small OpenCV preprocessing step (grayscale + denoise + threshold) to
	improve results on photographed ID cards.
	"""

	def extract(self, image_path: str) -> dict:
		image = cv2.imread(image_path)
		if image is None:
			raise RuntimeError(f"Could not read image at {image_path}")

		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		gray = cv2.medianBlur(gray, 3)
		_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

		raw_text = pytesseract.image_to_string(thresh).strip()

		data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
		confidences = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
		confidence = (sum(confidences) / len(confidences)) if confidences else 0.0

		return {"raw_text": raw_text, "confidence": round(confidence, 2)}
