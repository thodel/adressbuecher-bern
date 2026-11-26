"""Strasse, Hausnummer und Familienname (scripts/convert.py)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from convert import SAME, carry_heading, clean_street, own_surname, section_of, split_run_in  # noqa: E402


class Street(unittest.TestCase):
    def test_number_moves_to_its_field(self):
        self.assertEqual(clean_street("Bärenplatz 29", ""), ("Bärenplatz", "29"))
        self.assertEqual(clean_street("r. Neuve, 5", ""), ("r. Neuve", "5"))
        self.assertEqual(clean_street("Kramgasse 62", "62"), ("Kramgasse", "62"))

    def test_phone_marks_are_dropped(self):
        self.assertEqual(clean_street("pl. de la Gare. R T 180", ""), ("pl. de la Gare", ""))


class SameAddress(unittest.TestCase):
    def test_marks(self):
        for s in ("m. a", "m. a.", "m.a.", "dito"):
            self.assertTrue(SAME.match(s), s)
        self.assertFalse(SAME.match("Maupas"))


class Surname(unittest.TestCase):
    def test_wrong_inheritance_is_replaced(self):
        self.assertEqual(own_surname({"surname": "Hegner", "dash_prefix": "1", "text": "Grüter, Alfred."}), "Grüter")
        self.assertEqual(own_surname({"surname": "Roth", "dash_prefix": "1", "text": "— Rud., Sohn"}), "Roth")
        self.assertEqual(own_surname({"surname": "☎ Adler", "dash_prefix": "0", "text": "☎ Adler, Gasthaus"}), "Adler")


class FrakturBaende(unittest.TestCase):
    """Strom B (Gemini, 1861–1879): Fliesstext, fortgesetzte Rubrik, Zeile ohne Text."""

    def row(self, **kw):
        base = {"page": "184", "seq": "2", "heading": "Zimmermeister.", "text": "", "dash_prefix": "0",
                "surname": "", "alliance_name": "", "forename": "", "title": "", "civil_status": "",
                "occupation": "", "origin": "", "street": "", "building_no": "", "phone": "", "qa_flags": ""}
        return {**base, **kw}

    def test_fliesstext_wird_geteilt(self):
        r = self.row(text="Berger, L., Längg. 194. Blösch, A., zw. den Th. 184. Merz, J., Kramg. 202. "
                          "Weber, Marktg. 83. Zahnd, bei der Daube.")
        out = split_run_in(r)
        self.assertEqual([x["surname"] for x in out], ["Berger", "Blösch", "Merz", "Weber", "Zahnd"])
        self.assertEqual((out[2]["forename"], out[2]["street"], out[2]["building_no"]), ("J.", "Kramg", "202"))
        self.assertEqual(out[2]["seq"], "2.3")
        self.assertTrue(all("fliesstext" in x["qa_flags"] for x in out))

    def test_kurze_zeile_bleibt(self):
        r = self.row(text="Merz, J., Kramg. 202.")
        self.assertEqual(split_run_in(r), [r])

    def test_rubrik_nur_am_seitenanfang_fortgesetzt(self):
        rows = [self.row(page="1", heading="Schneider."), self.row(page="2", heading=""),
                self.row(page="2", heading="Seiler."), self.row(page="2", heading="")]
        out = carry_heading(rows)
        self.assertEqual([r["heading"] for r in out], ["Schneider.", "Schneider.", "Seiler.", ""])
        self.assertIn("rubrik_vorseite", out[1]["qa_flags"])

    def test_leere_zeile_behaelt_geerbten_namen(self):
        self.assertEqual(own_surname({"surname": "Jäggi", "dash_prefix": "1", "text": ""}), "Jäggi")

    def test_gleichheitszeichen_ist_allianz(self):
        self.assertEqual(own_surname({"surname": "Wattenwyl", "dash_prefix": "1", "text": "= v. Frisching F. C. F."}),
                         "Wattenwyl")


class Sections(unittest.TestCase):
    def test_outside(self):
        self.assertEqual(section_of(next(iter(__import__("convert").SECTIONS)), 1), "")


if __name__ == "__main__":
    unittest.main()
