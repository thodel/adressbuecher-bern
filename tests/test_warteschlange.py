"""Die Warteschlange scripts/weekly/queue.csv: Bern 1861–1914, ohne eingebundene Bände, nach Strom und Jahr.

    python3 -m unittest discover -s tests -v
"""
import csv
import importlib.util
import unittest
from pathlib import Path

WEEKLY = Path(__file__).resolve().parents[1] / "scripts" / "weekly"


def _mq():
    spec = importlib.util.spec_from_file_location("make_queue", WEEKLY / "make_queue.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Kennung(unittest.TestCase):
    def test_erstes_jahr_und_supplement(self):
        mq = _mq()
        self.assertEqual(mq.volume_id("Adressbuch der Stadt Bern: 1867-1868"), "1867")
        self.assertEqual(mq.volume_id("Adressbuch der Stadt Bern: 1893-1894.Suppl."), "1893s")
        self.assertEqual(mq.volume_id("Adressbuch der Stadt Bern: 1914"), "1914")


class Warteschlange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(csv.DictReader(open(WEEKLY / "queue.csv", encoding="utf-8")))

    def test_bern_1861_bis_1914_ohne_eingebundene(self):
        vols = [r["volume"] for r in self.rows]
        self.assertEqual(len(vols), len(set(vols)))
        self.assertTrue(all(1861 <= int(v[:4]) <= 1914 for v in vols))
        self.assertFalse({"1860", "1883", "1900"} & set(vols))
        self.assertEqual(len(self.rows), 37)

    def test_stroeme_nach_schrift(self):
        for r in self.rows:
            fraktur = int(r["volume"][:4]) <= 1879
            self.assertEqual((r["stream"], r["typeface"], r["reader"]),
                             ("B", "fraktur", "gemini") if fraktur else ("A", "antiqua", "qwen3.8"), r["volume"])

    def test_reihenfolge(self):
        self.assertEqual(self.rows, _mq().order(self.rows))
        self.assertEqual(self.rows[0]["volume"], "1881")
        self.assertEqual(self.rows[-1]["volume"], "1879")

    def test_manifest_und_liste_passen(self):
        ids = {r["erara_id"] for r in csv.DictReader(open(WEEKLY / "erara_liste.csv", encoding="utf-8"))}
        for r in self.rows:
            self.assertIn(r["erara_id"], ids)
            self.assertEqual(r["manifest"], f"https://www.e-rara.ch/i3f/v20/{r['erara_id']}/manifest")
            self.assertGreater(int(r["canvases"]), 100)


if __name__ == "__main__":
    unittest.main()
