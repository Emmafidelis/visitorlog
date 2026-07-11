import re

# Best-effort ID-number patterns per document type. Not exhaustive — this is
# a starting point for the human reviewer, never the final word. Unmatched
# fields are left blank rather than guessed.
_ID_NUMBER_PATTERNS = {
	"National ID": re.compile(r"\b(\d{8}-\d{5}-\d{5}-\d{2})\b"),  # Tanzanian NIDA format
	"Passport": re.compile(r"\b([A-Z]{1,2}\d{6,9})\b"),
	"Driving Licence": re.compile(r"\b([A-Z0-9]{6,12})\b"),
	"Voter ID": re.compile(r"\b(\d{6,12})\b"),
}

_NAME_LINE = re.compile(r"^[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3}$")

# Header/boilerplate text present on every ID of a given type (country name,
# document title, etc.) — would otherwise always be mistaken for the name
# since it's the first capitalized multi-word line on the document.
_BOILERPLATE_WORDS = {
	"republic", "united", "government", "national", "identity", "identification",
	"card", "passport", "licence", "license", "driving", "voter", "authority",
	"tanzania", "kenya", "uganda", "rwanda", "burundi",
}

# A label:value line is only treated as the name if the label itself says so —
# otherwise any other label with a title-cased value ("PLACE OF BIRTH: DAR ES
# SALAAM", "SEX: MALE") would be mistaken for a name line.
_NAME_LABEL_WORDS = {"name", "jina"}  # "jina" is Swahili for "name"


def parse_id_fields(raw_text: str, id_type: str | None = None) -> dict:
	"""Best-effort extraction of id_number/first_name/last_name from OCR text.

	Never invents data — anything that can't be confidently matched is left
	out of the returned dict for the human reviewer to fill in.
	"""
	fields = {}
	lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

	patterns_to_try = [_ID_NUMBER_PATTERNS[id_type]] if id_type in _ID_NUMBER_PATTERNS else list(
		_ID_NUMBER_PATTERNS.values()
	)
	for pattern in patterns_to_try:
		match = pattern.search(raw_text)
		if match:
			fields["id_number"] = match.group(1)
			break

	for line in lines:
		candidate = line
		if ":" in line:
			# ID cards commonly print the name after a label ("NAME: JOHN DOE").
			# Only treat the text after the colon as a name if the label says so —
			# otherwise a different label ("SEX: MALE") could be mistaken for one.
			label, _, value = line.partition(":")
			if not (_NAME_LABEL_WORDS & {word.lower() for word in label.split()}):
				continue
			candidate = value.strip()
		if not _NAME_LINE.match(candidate):
			continue
		if any(word.lower() in _BOILERPLATE_WORDS for word in candidate.split()):
			continue
		parts = candidate.split()
		fields["first_name"] = parts[0].title()
		if len(parts) > 2:
			fields["middle_name"] = " ".join(parts[1:-1]).title()
		fields["last_name"] = parts[-1].title()
		break

	return fields
