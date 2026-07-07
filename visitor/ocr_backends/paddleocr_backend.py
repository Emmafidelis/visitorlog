import threading

from visitor.ocr_backends.base import OCRBackend

_paddle_instance = None
_paddle_lock = threading.Lock()


def _get_paddle_ocr():
	global _paddle_instance
	if _paddle_instance is None:
		with _paddle_lock:
			if _paddle_instance is None:  # re-check: another thread may have built it while we waited
				try:
					from paddleocr import PaddleOCR
				except ImportError:
					raise RuntimeError(
						'PaddleOCR is not installed on this server. Run: '
						'./env/bin/pip install "visitor[paddleocr]", then restart bench.'
					)
				_paddle_instance = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
	return _paddle_instance


class PaddleOCRBackend(OCRBackend):
	"""Higher-accuracy backend for ID-card-style documents. Heavier install —
	opt in via Visitor Settings only after installing the paddleocr extra.
	"""

	def extract(self, image_path: str) -> dict:
		ocr = _get_paddle_ocr()
		result = ocr.ocr(image_path, cls=True)

		lines, confidences = [], []
		for page in result or []:
			for line in page or []:
				text, conf = line[1]
				lines.append(text)
				confidences.append(conf * 100)

		raw_text = "\n".join(lines)
		confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
		return {"raw_text": raw_text, "confidence": round(confidence, 2)}
