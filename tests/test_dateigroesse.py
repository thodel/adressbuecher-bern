"""GitHub warnt ab 50 MB und nimmt keine Datei über 100 MB an; ein Push mit so einer Datei scheitert erst beim Server.

Am 27.11.2026 war web/baende.csv mit 15 Bänden 57 MB gross (Warnung beim Push), und Strom A bringt 23 Bände mehr.
Seither liegt sie je Band in web/baende/<Band>.csv.gz (scripts/90_seite.py pack_other), wie in adressbuecher-zuerich.
Die Grenze hier liegt bei 50 MB, der Warnschwelle von GitHub.
"""

import csv
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRENZE = 50_000_000


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [f for f in out.decode().split("\0") if f]


class Dateigroesse(unittest.TestCase):
    def test_keine_datei_im_repo_ueber_50_mb(self):
        zu_gross = [(f, (ROOT / f).stat().st_size) for f in tracked()
                    if (ROOT / f).is_file() and (ROOT / f).stat().st_size > GRENZE]
        self.assertEqual(zu_gross, [], "über 50 MB: aufteilen oder packen")

    def test_baende_je_band(self):
        self.assertNotIn("web/baende.csv", tracked(), "alte Gesamtdatei gehört nicht ins Repo (nach web/baende/)")
        teile = {p.name.split(".")[0] for p in (ROOT / "web" / "baende").glob("*.csv.gz")}
        with (ROOT / "data" / "csv" / "00_volumes.csv").open(encoding="utf-8") as fh:
            baende = {r["volume"] for r in csv.DictReader(fh)}
        self.assertTrue(teile)
        self.assertLessEqual(teile, baende, "Teil ohne Band in 00_volumes.csv")


if __name__ == "__main__":
    unittest.main()
