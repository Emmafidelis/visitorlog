# Copyright (c) 2026, Aakvatech and contributors
# See license.txt

import unittest

from visitor.ocr_backends.id_parsers import parse_id_fields


class TestIdParsers(unittest.TestCase):
	def test_parses_national_id_number_and_skips_boilerplate_header(self):
		raw_text = "UNITED REPUBLIC OF TANZANIA\nNATIONAL ID\n\nJohn Mwangi\n\nID No 19900101-12345-00001-12"
		fields = parse_id_fields(raw_text, "National ID")

		self.assertEqual(fields["id_number"], "19900101-12345-00001-12")
		self.assertEqual(fields["first_name"], "John")
		self.assertEqual(fields["last_name"], "Mwangi")

	def test_never_invents_fields_it_cannot_find(self):
		fields = parse_id_fields("garbled unreadable text 4#!@", "National ID")
		self.assertNotIn("id_number", fields)
		self.assertNotIn("first_name", fields)

	def test_tries_all_patterns_when_id_type_unknown(self):
		raw_text = "Passport\nJane Doe\nP1234567"
		fields = parse_id_fields(raw_text, id_type=None)
		self.assertEqual(fields.get("id_number"), "P1234567")
