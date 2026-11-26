"""Lesungen (data/qwen/<Band>/entries.csv, data/gemini/<Band>/entries.csv) → Eintragsdateien im Schema von
adressbuecher-aarau. Der Leser steht je Band in parse_method (READER).

    python scripts/convert.py

Schreibt je Band data/csv/04_entries_<Band>.csv (Einwohner) und 04_berufe_<Band>.csv (Berufsregister),
dazu 03_sections.csv (welche Seiten in welchen Teil gehen) und 10_authority_links.csv (leer: Normdaten verknüpft
«Vernetzte Schweiz» über die Einheiten, nicht dieses Repo).

Übernommen werden nur das Einwohnerverzeichnis und das Berufsregister der Stadt; Inserate (Seiten mit
weniger als zehn Einträgen), Vorspann, Behörden, Häuserverzeichnisse und Querverweise nicht.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

import baende

ROOT = Path(__file__).resolve().parents[1]
QWEN = ROOT / "data" / "qwen"
GEMINI = ROOT / "data" / "gemini"
CSV = ROOT / "data" / "csv"

FIELDS = [
    "entry_id", "volume", "page", "section", "line_from", "line_to", "entry_type", "citizen_flag",
    "dash_prefix", "surname", "surname_inherited", "alliance_name", "maiden_name", "forename", "title",
    "civil_status", "relation", "occupation_raw", "origin_raw", "origin_canton", "address_seq",
    "address_role", "street_raw", "building_no", "phone_flag", "heading", "parse_method",
    "parse_confidence", "residual", "text", "municipality", "qa_flags",
]
AUTH_FIELDS = [
    "entry_id", "kind", "volume", "surname", "forename", "occupation", "origin", "qid", "label", "birth",
    "death", "hls_id", "gnd", "wd_description", "wd_occupations", "evidence", "score", "n_candidates",
    "tier", "hls_origins", "hls_head", "hls_check",
]
METHOD = {  # Leser → parse_method
    "qwen": "qwen3.8-27b, Bild 2x",  # Strom A und 1883, 1900 (PDF)
    "gemini": "gemini-3.5-flash (Antwort gemini-3.6-flash), IIIF bis 1600 px",  # Strom B, Fraktur 1861–1879
}


def reader(volume: str) -> str:
    """«gemini» oder «qwen»: wo die Lesung des Bands liegt (Strom B unter data/gemini/)."""
    return "gemini" if (GEMINI / volume / "entries.csv").exists() else "qwen"

# ── Aufbau der Bände ─────────────────────────────────────────────────────
# Seite = Seite im PDF (1883, 1900) bzw. Bildnummer bei e-rara (Canvas, 1-basiert; alle übrigen Bände).
# Geprüft an den ersten und letzten Einträgen und an den Seitenbildern davor und danach.
MUNICIPALITY = "Bern"
SECTIONS = {
    "1861": [("einwohner", 79, 145), ("berufe", 146, 184)],  # davor Versicherungsagenten, danach Wirthschaften
    "1862": [("einwohner", 87, 157), ("berufe", 158, 200)],  # davor Versicherungsagenten; Bild 201–202 Wirthschaften
                                                              # (bis 26.11.2026 mitgezählt, 68 Einträge)
    "1863": [("einwohner", 85, 156), ("berufe", 157, 200)],  # davor Versicherungsagenten, danach Wirthschaften
    # 1865: be_gemini --status nannte Einwohner 94–173, Berufe 174–220; das Berufsregister beginnt aber auf
    # Bild 170 (Druckseite 160) und endet auf 218, Bild 219–220 sind Wirthschaften.
    "1865": [("einwohner", 94, 169), ("berufe", 170, 218)],  # davor Versicherungsagenten
    # 1864–1879: am Bild geprüft (Titel «VIII. Alphabetisches Verzeichniß der ständigen Einwohner» und «IX. Verzeichniß
    # der Künstler, Handels- und Gewerbsleute», davor Versicherungsagenten, danach «X. Wirthschaften»). Abweichend von
    # be_gemini --status: 1866 und 1868 enden die Berufe vor den Wirthschaften (Bild 238, 274), 1875 und 1879 beginnen
    # sie früher (Bild 279, 278). Ab 1873 beginnen die Wirthschaften auf derselben Seite (cut_wirthschaften).
    # 1864: das Berufsregister geht auf Bild 213 weiter (Zügler, Zurichter), das Strom B nicht gelesen hat.
    # "1864": [("einwohner", 91, 165), ("berufe", 166, 212)],  zurückgestellt 26.11.2026: Stichprobe 15/20 (75 %; vier Lesefehler in Namen, eine Rubrik leer) und Bild 213 ungelesen
    "1866": [("einwohner", 101, 186), ("berufe", 187, 238)],
    "1867": [("einwohner", 106, 200), ("berufe", 201, 255)],  # nach grösserer Stichprobe übernommen (66/80, 26.11.2026)
    "1868": [("einwohner", 113, 214), ("berufe", 215, 274)],
    "1870": [("einwohner", 117, 236), ("berufe", 237, 296)],
    "1871": [("einwohner", 123, 242), ("berufe", 243, 301)],
    "1873": [("einwohner", 131, 249), ("berufe", 250, 308)],
    "1875": [("einwohner", 145, 278), ("berufe", 279, 342)],
    "1877": [("einwohner", 138, 283), ("berufe", 284, 354)],
    "1879": [("einwohner", 138, 277), ("berufe", 278, 355)],
    "1883": [("einwohner", 83, 192), ("berufe", 193, 246)],
    "1900": [("einwohner", 142, 385), ("berufe", 386, 491)],
}

MIN_ENTRIES = 10  # weniger Einträge auf einer Seite: Inserat oder Zwischenseite
MIN_ENTRIES_GEMINI = 3
NOT_ENTRY = re.compile(r"siehe auch|voir aussi|^\(?(?:Siehe|Voir)\b|Abkürzungen|Abréviations|"
                       r"alphabetischen Reihenfolge|Telephonzeichen|La lettre R\.", re.I)
FIRM = re.compile(r"&|\bCie\b|\bC°|\bGebr(?:\.|üder)|\bfrères\b|A\.-?G\.|\bAG\b|S\. ?A\.|Aktiengesellschaft|"
                  r"Société|Genossenschaft|Verein\b|Gesellschaft|Fabri(?:k|que)\b|Kasse\b|Caisse\b|Banque\b|"
                  r"Bank\b|Werke?\b|Erben\b|hoirie\b", re.I)
WIDOW = re.compile(r"\bWwe\.?|\bWitwe\b|\bWittwe\b|\bveuve\b", re.I)
DASH = re.compile(r"^\s*[—–=-]")  # «=» in den Fraktur-Bänden: Allianzname zum vorigen Familiennamen
LEAD = re.compile(r"^[\s*†§☎„\"'«»(]+")
SAME = re.compile(r"^(?:m\. ?a\.?|même adresse|dito|ditto|do\.?|id\.?|ebenda|ebd\.?)$", re.I)


# Fliesstext im Berufsregister (1861, S. 166–184): das Modell gab einen Absatz mit vielen Personen als einen
# Eintrag. Geteilt wird nach «<Nummer>. <Name>,»; jedes Stück wird zu einem Eintrag (qa_flags «fliesstext»).
RUN_IN = re.compile(r"(?<=\d\.)\s+(?=(?:v\. |de )?[A-ZÄÖÜ][\wäöüßéè'\-]+,)|"
                    r"(?<=\d [a-z]\.)\s+(?=(?:v\. |de )?[A-ZÄÖÜ][\wäöüßéè'\-]+,)")
STAND = re.compile(r"^(?:geb\.|Wwe\.?|Wittwe|Witwe|Frau|Jgfr\.?|Fräul\.?|Schwest\.?|Gebr\.?)", re.I)


def split_run_in(r: dict) -> list[dict]:
    """Einen Fliesstext-Absatz in Einträge teilen; Stücke ohne Komma (Rest der Vorseite) fallen weg."""
    parts = RUN_IN.split(r["text"])
    if len(parts) < 2 or len(r["text"]) <= 80:
        return [r]
    out = []
    for i, part in enumerate(parts):
        bits = [b.strip() for b in part.strip().rstrip(".").split(",")]
        if len(bits) < 2 or not bits[0]:
            continue
        m = re.match(r"^(.*?)[\s.]*(\d+\s?[a-z]?(?:/\d+)?)?$", bits[-1])
        street, number = (m.group(1).strip(" ."), m.group(2) or "") if m else (bits[-1], "")
        mid = bits[1:-1]
        stand = [b for b in mid if STAND.match(b)]
        rest = [b for b in mid if b not in stand]
        out.append({**r, "seq": f"{r['seq']}.{i + 1}", "text": part.strip(), "dash_prefix": "0",
                    "surname": bits[0], "alliance_name": "", "forename": rest[0] if rest else "",
                    "title": "", "civil_status": ", ".join(stand), "occupation": ", ".join(rest[1:]),
                    "street": street, "building_no": number.replace(" ", ""), "phone": "",
                    "qa_flags": ";".join(f for f in (r["qa_flags"], "fliesstext") if f)})
    return out or [r]


# Abschnitt «X. Wirthschaften» (a. Gasthäuser, b. Cafés, c. Speisewirthschaften, d. Badwirthschaften) beginnt ab
# 1873 auf der letzten Seite des Berufsregisters (1873 Bild 308, 1875 342, 1877 354, 1879 355).
WIRTHSCHAFTEN = re.compile(r"^[a-e]\.\s*(Gasth|Caf|Speise|Bad)")


def cut_wirthschaften(rows: list[dict]) -> list[dict]:
    """Berufsregister bis zur ersten Rubrik des Abschnitts Wirthschaften; was danach kommt, gehört nicht dazu."""
    for i, r in enumerate(rows):
        if WIRTHSCHAFTEN.match(r["heading"].strip()):
            return rows[:i]
    return rows


def carry_heading(rows: list[dict]) -> list[dict]:
    """Berufsregister von Strom B: Einträge oben auf einer Seite ohne Rubrik setzen die letzte Rubrik der
    Vorseite fort (das Modell nennt die Rubrik nur, wo sie gedruckt steht). Eine Lücke mitten auf der Seite
    bleibt leer: dort fehlt eher eine Überschrift (1862 S. 192). Gesetzte Rubriken: qa_flags «rubrik_vorseite»."""
    out, last, page, top = [], "", None, True
    for r in rows:
        if r["page"] != page:
            page, top = r["page"], True
        if r["heading"].strip():
            top, last = False, r["heading"]
        elif top and last:
            r = {**r, "heading": last, "qa_flags": ";".join(f for f in (r["qa_flags"], "rubrik_vorseite") if f)}
        out.append(r)
    return out


def section_of(volume: str, page: int) -> str:
    for name, a, b in SECTIONS[volume]:
        if a <= page <= b:
            return name
    return ""


def own_surname(r: dict) -> str:
    """Familienname; ein vom Vorgänger geerbter Name, der zum Text nicht passt, wird ersetzt."""
    sn = LEAD.sub("", r["surname"]).strip()
    text = LEAD.sub("", r["text"])
    if r["dash_prefix"] == "1" and text and not DASH.match(text) and sn and sn not in text:
        return re.split(r"[,(]", text)[0].strip(" .")
    return sn


def clean_street(street: str, number: str) -> tuple[str, str]:
    """Strasse ohne Telefonzeichen und ohne doppelte Hausnummer; «Bärenplatz 29» → («Bärenplatz», «29»)."""
    for _ in range(2):  # «… R T 180»: erst die Telefonnummer, dann das R.
        street = re.sub(r"\s*(?:\bH\.|☎.*|\bT\s?\d+.*|\bR\.?\s*$|\bR?\s?T\.?\s*$)", "", street).strip(" ,.")
    number = number.strip(" ,.")
    if number:
        street = re.sub(rf"[\s,]+{re.escape(number)}\s*$", "", street)
    else:
        m = re.match(r"^(.*\D)[\s,]+(\d+\s?[a-z]?)$", street)
        if m:
            street, number = m.group(1).strip(" ,"), m.group(2).replace(" ", "")
    return street, number


def convert(volume: str) -> tuple[list[dict], Counter]:
    src = GEMINI if reader(volume) == "gemini" else QWEN
    rows = list(csv.DictReader(open(src / volume / "entries.csv", encoding="utf-8")))
    if reader(volume) == "gemini":
        rows = [x for r in rows for x in (split_run_in(r) if section_of(volume, int(r["page"])) == "berufe" else [r])]
        berufe = carry_heading(cut_wirthschaften([r for r in rows if section_of(volume, int(r["page"])) == "berufe"]))
        rows = [r for r in rows if section_of(volume, int(r["page"])) != "berufe"] + berufe
    pages = Counter(int(r["page"]) for r in rows)
    # Strom B liest nur die Seiten der Verzeichnisse (be_gemini.py klassiert vorher); die letzte Seite eines
    # Teils hat oft weniger als zehn Einträge (1861 S. 145: neun).
    min_entries = MIN_ENTRIES if reader(volume) == "qwen" else MIN_ENTRIES_GEMINI
    out, stats = [], Counter()
    last = ("", "")  # Adresse des vorigen Eintrags, für «m. a.» (même adresse)
    for r in rows:
        page = int(r["page"])
        seq, _, sub = r["seq"].partition(".")  # «5.3»: drittes Stück des Fliesstexts in Zeile 5
        seq = int(seq)
        sec = section_of(volume, page)
        if not sec:
            stats["ausserhalb der Verzeichnisse"] += 1
            continue
        if pages[page] < min_entries:
            stats["Inserat- oder Zwischenseite"] += 1
            continue
        if NOT_ENTRY.search(r["text"]):
            stats["Querverweis oder Vorbemerkung"] += 1
            continue
        surname, alliance = own_surname(r), r["alliance_name"]
        if " = " in surname:  # «v. Bonstetten = de Bigneule»: Familienname = Allianzname
            surname, _, rest = surname.partition(" = ")
            alliance = alliance or rest.strip()
        if not surname or len(surname.split()) > 4:
            stats["ohne Familienname"] += 1
            continue
        street, number = clean_street(r["street"], r["building_no"])
        if SAME.match(street):
            street, number = last
            stats["Adresse vom vorigen Eintrag"] += 1
        last = (street, number)
        flags = [f for f in r["qa_flags"].split(";") if f]
        if not r["text"].strip():
            flags.append("ohne_text")  # das Modell gab nur die Felder, nicht die Zeile
        firm = bool(FIRM.search(f"{surname} {r['forename']} {r['text'][:60]}")) and not WIDOW.search(r["text"])
        out.append({
            "entry_id": f"{volume}-{sec}-{page:03d}-{seq:03d}" + (f"-{int(sub):02d}" if sub else ""),
            "volume": volume, "page": page,
            "section": sec, "line_from": seq, "line_to": seq,
            "entry_type": "firma" if firm else "person", "citizen_flag": "",
            "dash_prefix": r["dash_prefix"], "surname": surname,
            "surname_inherited": "1" if r["dash_prefix"] == "1" and DASH.match(r["text"]) else "",
            "alliance_name": alliance, "maiden_name": "", "forename": r["forename"].strip(" .,"),
            "title": r["title"], "civil_status": r["civil_status"], "relation": "",
            "occupation_raw": r["occupation"], "origin_raw": r["origin"], "origin_canton": "",
            "address_seq": "1", "address_role": "", "street_raw": street, "building_no": number,
            "phone_flag": "1" if r["phone"].strip() or "☎" in r["text"] else "", "heading": r["heading"],
            "parse_method": METHOD[reader(volume)],
            "parse_confidence": "medium" if {"street_rare", "hyphen", "unreadable", "surname_split", "fliesstext",
                                              "ohne_text"} & set(flags)
            else "high",
            "residual": "", "text": r["text"], "municipality": MUNICIPALITY, "qa_flags": ";".join(flags),
        })
        stats[sec] += 1
    return out, stats


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    sections = []
    CSV.mkdir(parents=True, exist_ok=True)
    for old in ("04_entries.csv", "04_berufe.csv"):  # bis 26.11.2026 alle Bände in einer Datei
        (CSV / old).unlink(missing_ok=True)
    for volume in SECTIONS:
        rows, stats = convert(volume)
        for teil in ("einwohner", "berufe"):
            write(baende.datei(teil, volume, CSV), [r for r in rows if r["section"] == teil], FIELDS)
        sections += [{"volume": volume, "section": n, "page_from": a, "page_to": b} for n, a, b in SECTIONS[volume]]
        print(volume, dict(sorted(stats.items())))
    write(CSV / "03_sections.csv", sections, ["volume", "section", "page_from", "page_to"])
    write(CSV / "10_authority_links.csv", [], AUTH_FIELDS)

if __name__ == "__main__":
    main()
