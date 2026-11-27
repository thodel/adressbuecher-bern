"""Der Leser scripts/weekly/be_weekly.py: Reihenfolge, Seitenbereiche, Vorrang für Zürich.

    python3 -m unittest discover -s tests -v
"""
import csv
import importlib.util
import unittest
from pathlib import Path

WEEKLY = Path(__file__).resolve().parents[1] / "scripts" / "weekly"


def _bw():
    spec = importlib.util.spec_from_file_location("be_weekly", WEEKLY / "be_weekly.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rows(parts):
    """parts: {(von, bis): teil} → Zuordnung je Seite, Rest «andere»."""
    n = max(b for _, b in parts)
    out = [{"page": p, "part": "andere"} for p in range(1, n + 1)]
    for (a, b), t in parts.items():
        for p in range(a, b + 1):
            out[p - 1]["part"] = t
    return out


class Reihenfolge(unittest.TestCase):
    def setUp(self):
        self.bw = _bw()
        self.queue = list(csv.DictReader(open(WEEKLY / "queue.csv", encoding="utf-8")))

    def test_erster_band_1881_dann_1886(self):
        self.assertEqual(self.bw.next_volume(self.queue, {})["volume"], "1881")
        self.assertEqual(self.bw.next_volume(self.queue, {"1881": {}})["volume"], "1886")

    def test_nur_strom_a(self):
        st = {q["volume"]: {} for q in self.queue if q["stream"] == "A"}
        self.assertIsNone(self.bw.next_volume(self.queue, st))

    def test_only_waehlt_den_band(self):
        self.assertEqual(self.bw.next_volume(self.queue, {}, "1905")["volume"], "1905")
        self.assertIsNone(self.bw.next_volume(self.queue, {}, "1861"))   # Fraktur, Strom B


class Seitenbereiche(unittest.TestCase):
    def setUp(self):
        self.bw = _bw()

    def test_groesster_block_mit_inserat_luecken(self):
        rows = _rows({(20, 100): "einwohner", (101, 104): "inserate", (105, 180): "einwohner",
                      (190, 260): "berufe", (300, 302): "einwohner"})
        self.assertEqual(self.bw.sections(rows), {"einwohner": [20, 180], "berufe": [190, 260]})

    def test_berufe_ueberlappen_nie(self):
        rows = _rows({(10, 50): "einwohner", (45, 47): "berufe", (51, 90): "berufe"})
        rows[46]["part"] = "einwohner"
        self.assertEqual(self.bw.sections(rows)["berufe"][0], 51)

    def test_kein_einwohnerteil(self):
        self.assertNotIn("einwohner", self.bw.sections(_rows({(1, 3): "einwohner", (4, 40): "behoerden"})))


class Vorrang(unittest.TestCase):
    def test_wartet_auf_zuerich_und_jeden_lesedurchgang(self):
        bw = _bw()
        self.assertIn("zh_weekly.py", bw.OTHERS.split("|"))
        self.assertIn("run_qwen.py", bw.OTHERS.split("|"))

    def test_bildbreite_halber_scan_1100_bis_1200(self):
        bw = _bw()
        self.assertEqual(bw.read_width([{"width": 1791}] * 3), 1100)   # 1881: 800 px las schlechter
        self.assertEqual(bw.read_width([{"width": 2300}] * 3), 1150)
        self.assertEqual(bw.read_width([{"width": 3000}] * 3), 1200)

    def test_canvases_aus_erara_manifest(self):
        bw = _bw()
        m = {"sequences": [{"canvases": [{"@id": "c1", "label": "1", "width": 1619, "images": [
            {"resource": {"service": {"@id": "https://www.e-rara.ch/i3f/v20/3012394"}}}]}]}]}
        self.assertEqual(bw.canvases(m)[0]["iiif_image"], "https://www.e-rara.ch/i3f/v20/3012394")


if __name__ == "__main__":
    unittest.main()


class Serverfehler(unittest.TestCase):
    """27.11.2026: GPUStack antwortete 504/500; der Lauf markierte alle 23 Bände als «fehler» und lief nicht mehr."""

    def test_transient(self):
        import socket
        import urllib.error
        bw = _bw()
        for e in (urllib.error.HTTPError("u", 504, "Gateway Time-out", {}, None),
                  urllib.error.HTTPError("u", 500, "Internal Server Error", {}, None),
                  urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None),
                  urllib.error.URLError("down"), TimeoutError(), socket.timeout(), ConnectionResetError()):
            self.assertTrue(bw.transient(e), e)
        for e in (urllib.error.HTTPError("u", 404, "Not Found", {}, None), ValueError("x"), KeyError("canvases")):
            self.assertFalse(bw.transient(e), e)

    def _lauf(self, fehler):
        import tempfile
        import urllib.error  # noqa: F401
        bw = _bw()
        d = Path(tempfile.mkdtemp())
        with open(d / "queue.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["volume", "stream"]); w.writerows([["1881", "A"], ["1886", "A"], ["1888", "A"]])
        bw.HERE, bw.STATE = d, d / "state.json"
        bw.log = lambda msg: None
        bw.load_env = lambda: None
        bw.busy = lambda: False
        bw.next_volume = lambda queue, st, only: next((q for q in queue if q["volume"] not in st), None)
        tried = []

        def process(q, st):
            tried.append(q["volume"]); st[q["volume"]] = {"status": "läuft"}; raise fehler
        bw.process = process
        import sys
        argv, sys.argv = sys.argv, ["be_weekly.py"]
        try:
            bw.main()
        finally:
            sys.argv = argv
        return tried, bw.load_state()

    def test_serverfehler_beendet_den_lauf_ohne_markierung(self):
        import urllib.error
        tried, st = self._lauf(urllib.error.HTTPError("u", 504, "Gateway Time-out", {}, None))
        self.assertEqual(tried, ["1881"])           # nicht durch alle Bände
        self.assertNotIn("1881", st)                # nächster Lauf nimmt 1881 wieder

    def test_anderer_fehler_markiert_und_geht_weiter(self):
        tried, st = self._lauf(KeyError("canvases"))
        self.assertEqual(tried, ["1881", "1886", "1888"])
        self.assertTrue(st["1881"]["status"].startswith("fehler"))
