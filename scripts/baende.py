"""Bände und Eintragsdateien: eine Datei je Band und Teil (data/csv/04_entries_<Band>.csv, 04_berufe_<Band>.csv).

Die Bandliste steht in data/csv/00_volumes.csv. Kennungen sind Zeichenketten («1883», «1893s» für ein
Supplement); `jahr()` gibt das Jahr als Zahl. Wie adressbuecher-zuerich seit c2eabb4: alle Bände in einer
Datei würden die Grenze von GitHub (100 MB) überschreiten.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"
TEIL = {"einwohner": "04_entries", "berufe": "04_berufe"}


def jahr(volume: str) -> int:
    return int(volume[:4])


def ordnung(volume: str) -> tuple[int, str]:
    return jahr(volume), volume[4:]


def volumes() -> dict[str, dict]:
    """Band → Zeile aus 00_volumes.csv, aufsteigend nach Jahr."""
    with (CSV_DIR / "00_volumes.csv").open(encoding="utf-8") as fh:
        rows = {r["volume"]: r for r in csv.DictReader(fh)}
    return {v: rows[v] for v in sorted(rows, key=ordnung)}


def label(volume: str, title: str = "") -> str:
    """«1883–84» für einen Doppeljahrgang im Titel («… 1883-1884»), sonst die Kennung."""
    m = re.search(r"(\d{4})\s*[-–]\s*(\d{4})\s*$", title)
    if m and m.group(1) == volume[:4]:
        return f"{m.group(1)}–{m.group(2)[2:]}"
    return volume


def datei(teil: str, volume: str, csv_dir: Path = CSV_DIR) -> Path:
    return csv_dir / f"{TEIL[teil]}_{volume}.csv"


def dateien(teil: str, csv_dir: Path = CSV_DIR) -> list[Path]:
    """Alle Dateien eines Teils, nach Band geordnet."""
    pat = re.compile(rf"^{TEIL[teil]}_(\d{{4}}[a-z]?)\.csv$")
    found = [(m.group(1), p) for p in csv_dir.glob(f"{TEIL[teil]}_*.csv") if (m := pat.match(p.name))]
    return [p for _v, p in sorted(found, key=lambda t: ordnung(t[0]))]


def lies(teil: str, csv_dir: Path = CSV_DIR) -> list[dict]:
    rows: list[dict] = []
    for p in dateien(teil, csv_dir):
        with p.open(encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    return rows


def menu(volumes, default: str, labels: dict[str, str] | None = None, alle: str = "alle Bände (gross)") -> str:
    """Die <option> eines Bandmenüs: neuester Band zuerst, nach Jahr; der Standardband ist vorgewählt,
    «alle Bände» steht am Ende. Bis 26.11.2026 standen die Menüs von Hand im HTML."""
    labels = labels or {}
    vs = sorted(volumes, key=ordnung, reverse=True)
    return "".join(f'<option value="{v}"{" selected" if v == default else ""}>{labels.get(v, v)}</option>'
                   for v in vs) + f'<option value="">{alle}</option>'
