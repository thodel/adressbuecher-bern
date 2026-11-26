"""Bände und Dateien je Band (scripts/baende.py), Bandmenüs von Seite und Karte.

Seit 26.11.2026 schreibt convert.py je Band 04_entries_<Band>.csv und 04_berufe_<Band>.csv (vorher je eine
Datei für alle Bände); die Bandliste steht in data/csv/00_volumes.csv.

    python3 -m unittest discover -s tests -v
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import baende  # noqa: E402


class Kennungen(unittest.TestCase):
    def test_supplement_nach_dem_band(self):
        self.assertEqual(sorted(["1900", "1893s", "1861", "1893"], key=baende.ordnung), ["1861", "1893", "1893s", "1900"])
        self.assertEqual(baende.jahr("1896s"), 1896)

    def test_label_doppeljahrgang(self):
        self.assertEqual(baende.label("1883", "Adressbuch der Stadt Bern 1883-1884"), "1883–84")
        self.assertEqual(baende.label("1861", "Adressbuch der Stadt Bern: 1861"), "1861")

    def test_dateien_nach_band_ohne_fremde(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ("04_entries_1900.csv", "04_entries_1893s.csv", "04_entries_1861.csv", "04_entries.csv",
                      "04_entries_probe.csv", "04_berufe_1861.csv"):
                (Path(d) / n).write_text("volume\n", encoding="utf-8")
            self.assertEqual([p.name for p in baende.dateien("einwohner", Path(d))],
                             ["04_entries_1861.csv", "04_entries_1893s.csv", "04_entries_1900.csv"])


class Daten(unittest.TestCase):
    def test_je_band_beide_dateien_und_nur_der_band(self):
        vols = baende.volumes()
        for teil in ("einwohner", "berufe"):
            names = {p.name for p in baende.dateien(teil)}
            self.assertEqual(names, {baende.datei(teil, v).name for v in vols}, teil)
        self.assertFalse((baende.CSV_DIR / "04_entries.csv").exists())
        self.assertFalse((baende.CSV_DIR / "04_berufe.csv").exists())

    def test_dateien_unter_github_grenze(self):
        for p in baende.CSV_DIR.glob("*.csv"):
            self.assertLess(p.stat().st_size, 95e6, p.name)


class Bandmenue(unittest.TestCase):
    def test_absteigend_neuester_vorgewaehlt(self):
        html = baende.menu(["1883", "1900", "1861", "1893s"], "1900", {"1883": "1883–84"})
        werte = re.findall(r'<option value="(\d{4}s?)"', html)
        self.assertEqual(werte, ["1900", "1893s", "1883", "1861"])
        self.assertEqual(re.findall(r'<option value="(\d{4}s?)" selected', html), ["1900"])
        self.assertIn(">1883–84<", html)
        self.assertTrue(html.endswith('<option value="">alle Bände (gross)</option>'))

    def test_kein_handgeschriebenes_menue(self):
        for f in ("90_seite.py", "92_karte.py"):
            src = (ROOT / "scripts" / f).read_text(encoding="utf-8")
            self.assertNotRegex(src, r'<select id="vol"[^>]*><option', f)
            self.assertNotIn("['1883', '1900']", src, f)


if __name__ == "__main__":
    unittest.main()
