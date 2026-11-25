"""Warteschlange der fehlenden Berner Bände 1861–1914 (scripts/weekly/README.md).

    python3 scripts/weekly/make_queue.py      # erara_liste.csv → queue.csv (holt die IIIF-Manifeste bei e-rara)

`erara_liste.csv` nennt je Band die e-rara-ID aus der Reihe «Adressbuch der Stadt Bern»
(doi:10.3931/e-rara-4614, UB Bern, Public Domain Mark). Je Band wird das IIIF-Manifest geholt
(Zahl der Bilder, Grösse des ersten Bildes). Gelesen wird später über IIIF, nicht aus einem PDF.

Band-Kennung: erstes Jahr des Titels («1867-1868» → 1867); Supplemente bekommen ein «s» («1893s»).
Schrift: bis 1879 Fraktur (Gemini), ab 1881 Antiqua (qwen3.8). Geprüft am 25.11.2026 an Seiten aus
1861, 1877, 1879 (Fraktur) und 1881, 1886–87, 1899 (Antiqua).

Reihenfolge und Ströme:
- `A` Antiqua 1881–1914, aufsteigend, qwen3.8 auf tei;
- `B` Fraktur 1861–1879, aufsteigend, Gemini.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "adressbuecher-bern (Universitaet Bern, DH)"}
DONE = {"1860", "1883", "1900"}  # 1883–84 und 1900 eingebunden; 1860 liegt als PDF vor, Probe zu schwach
FRAKTUR_BIS = 1879
FIELDS = ["volume", "stream", "reader", "typeface", "title", "erara_id", "manifest", "canvases", "width", "height"]


def volume_id(title: str) -> str:
    """«Adressbuch der Stadt Bern: 1893-1894.Suppl.» → «1893s»; «…: 1867-1868» → «1867»."""
    m = re.search(r":\s*(1[89]\d\d)", title)
    if not m:
        raise ValueError(f"kein Jahr im Titel: {title}")
    return m.group(1) + ("s" if "suppl" in title.lower() else "")


def entry(erara_id: str, title: str, manifest: dict) -> dict:
    v = volume_id(title)
    fraktur = int(v[:4]) <= FRAKTUR_BIS
    canvases = manifest["sequences"][0]["canvases"]
    return {"volume": v, "stream": "B" if fraktur else "A", "reader": "gemini" if fraktur else "qwen3.8",
            "typeface": "fraktur" if fraktur else "antiqua", "title": title, "erara_id": erara_id,
            "manifest": f"https://www.e-rara.ch/i3f/v20/{erara_id}/manifest", "canvases": len(canvases),
            "width": canvases[0]["width"], "height": canvases[0]["height"]}


def order(rows: list[dict]) -> list[dict]:
    """Zuerst Strom A, dann B; je Strom nach Jahr, das Supplement nach seinem Band."""
    return sorted(rows, key=lambda r: (r["stream"], int(r["volume"][:4]), r["volume"]))


def fetch(erara_id: str) -> dict:
    req = urllib.request.Request(f"https://www.e-rara.ch/i3f/v20/{erara_id}/manifest", headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main() -> None:
    rows = []
    for r in csv.DictReader(open(HERE / "erara_liste.csv", encoding="utf-8")):
        if volume_id(r["titel"]) in DONE:
            continue
        rows.append(entry(r["erara_id"], r["titel"], fetch(r["erara_id"])))
        time.sleep(0.5)
    rows = order(rows)
    with open(HERE / "queue.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    n = {s: sum(1 for r in rows if r["stream"] == s) for s in "AB"}
    print(f"queue.csv: {len(rows)} Bände (A {n['A']}, B {n['B']}), {sum(r['canvases'] for r in rows)} Bilder",
          file=sys.stderr)


if __name__ == "__main__":
    main()
