"""Der Fraktur-Lauf scripts/weekly/be_gemini.py: Kosten je Antwort und Schutz gegen zu teure Seiten.

    python3 -m unittest discover -s tests -v
"""
import importlib.util
import sys
import unittest
from pathlib import Path

WEEKLY = Path(__file__).resolve().parents[1] / "scripts" / "weekly"


def _bg():
    sys.path.insert(0, str(WEEKLY))
    spec = importlib.util.spec_from_file_location("be_gemini", WEEKLY / "be_gemini.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Kosten(unittest.TestCase):
    def test_denk_token_zaehlen_als_ausgabe(self):
        bg = _bg()
        u = {"promptTokenCount": 1_000_000, "candidatesTokenCount": 0}
        self.assertAlmostEqual(bg.cost(u), 1.50)
        self.assertAlmostEqual(bg.cost({"candidatesTokenCount": 500_000, "thoughtsTokenCount": 500_000}), 9.00)


class Schluessel(unittest.TestCase):
    def test_leer_und_steuerzeichen_weg(self):
        bg = _bg()
        self.assertEqual(bg.clean_key(' "AQ.abcDEF_123-xyz.0987654321"   \t'), "AQ.abcDEF_123-xyz.0987654321")
        self.assertEqual(bg.clean_key(""), "")


class Schutz(unittest.TestCase):
    def setUp(self):
        self.bg = _bg()

    def test_vor_der_probe_kein_halt(self):
        self.assertEqual(self.bg.guard([0.2] * 19), "")

    def test_zu_teuer_nach_der_probe(self):
        self.assertIn("je Seite", self.bg.guard([0.09] * 20))
        self.assertEqual(self.bg.guard([0.05] * 20), "")

    def test_budget(self):
        self.assertIn("Budget", self.bg.guard([0.05] * 7001))

    def test_nur_strom_b_und_fraktur_anweisung(self):
        self.assertEqual(self.bg.STREAM, "B")
        self.assertIn("lange s (ſ)", self.bg.PROMPT)

    def test_bildbreite_hoechstens_1600(self):
        self.assertEqual(self.bg.width_of({"width": 1395}), 1395)
        self.assertEqual(self.bg.width_of({"width": 1811}), 1600)


if __name__ == "__main__":
    unittest.main()
