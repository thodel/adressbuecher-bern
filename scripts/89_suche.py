"""89_suche.py — Startseite mit Suche über alle Bände und Eintragsseiten (scripts/site_search.py).

    python scripts/89_suche.py --out _site

Nimmt die Tabellen der Kontrollseite (scripts/90_seite.py: TABS, load_rows() mit Telefon, anderen Bänden und
Normdaten, die Bandliste aus 00_volumes.csv und web/erara_pages.csv für die Links auf e-rara) und die
Strassenpunkte aus web/geo/streets.csv (WGS84, Schlüssel wie street_key). Die Kontrollseite selbst liegt unter
korrektur/. Zurückgestellte Bände stehen nicht in 00_volumes.csv und fehlen darum hier wie dort.
"""
from __future__ import annotations

import argparse
import csv
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_nav  # noqa: E402
import site_search  # noqa: E402

K = importlib.import_module("90_seite")
ERARA_PAGE = "https://www.e-rara.ch/bes_1/periodical/pageview/"

CITY = {
    "key": "bern", "name": "Bern", "span": K.span(K.VOLUMES), "lang": "de",
    "title": "Adressbücher der Stadt Bern",
    "lead": f"Einwohner und Berufsregister aus den Adressbüchern der Stadt Bern {K.span(K.VOLUMES)}, maschinell "
            "gelesen und in Felder zerlegt. Gesucht wird über alle Bände.",
    "tagline": "Adressbücher · Einwohner · Berufe",
    "repo": K.REPO_URL, "center": [46.9480, 7.4474],
    "korr": "korrektur/?tab={part}&vol={vol}&q={id}",
    "nav": [["karte.html", "Karte: Wohnorte nach Strassen"], ["abdeckung.html", "Abdeckung"]],
    "note": "Quellen: Adressbücher der Stadt Bern, Scans auf e-rara (Universitätsbibliothek Bern). Gelesen mit "
            "qwen3.8 (Universität Bern; 1883–84 und 1900) bzw. Gemini 3.5 Flash (übrige Bände), nicht von Hand "
            "korrigiert; im Zweifel gilt die Seite auf e-rara.",
    "page_note": "Die Seitenbilder liegen auf e-rara und werden nur verlinkt; «Seite» ist die gedruckte Seitenzahl.",
    "parts": {k: label for k, label, *_ in K.TABS},
    "volumes": dict(K.VOL_LABEL),
}
CORE = {"entry_id", "volume", "page", "surname", "forename", "alliance_name", "maiden_name", "occupation_raw",
        "street_raw", "building_no", "origin_raw", "title", "heading", "text", "telefon", "other_volume", "authority",
        "zeitreise", "street_key", "municipality"}


def streets() -> dict[tuple[str, str], tuple[float, float]]:
    """(Gemeinde, Strassenschlüssel) → (lat, lon), wie 92_karte.py aus web/geo/streets.csv (+ streets_manual.csv)."""
    out = {}
    for name in ("streets.csv", "streets_manual.csv"):
        p = Path("web/geo") / name
        if p.exists():
            for r in csv.DictReader(p.open(encoding="utf-8")):
                if r["lat"]:
                    out[(r["municipality"], r["street_norm"])] = (float(r["lat"]), float(r["lon"]))
    return out


def links_for(r: dict) -> tuple[list, list]:
    """Telefon im gemeinsamen Format (std_links); Normdaten «Stufe|Label|Leben|HLS|QID|GND|Feld|Notiz» und andere
    Bände «Stufe|Band|entry_id|Text|Belege» (Reihenfolge von 90_seite.py, nicht die von std_links)."""
    links, _ = site_search.std_links({"telefon": r.get("telefon", "")})
    if r.get("authority"):
        tier, label, life, hls, qid, gnd, field, note = (r["authority"].split("|") + [""] * 8)[:8]
        what = " · ".join(x for x in (life, field, note, f"{tier}, ungeprüft") if x)
        if qid:
            links.append(["wd", label or qid, f"https://www.wikidata.org/wiki/{qid}", f"{what} · Wikidata"])
        if hls:
            links.append(["hls", f"HLS {hls}", f"https://hls-dhs-dss.ch/de/articles/{hls}/", "Historisches Lexikon der Schweiz"])
        if gnd:
            links.append(["ext", f"GND {gnd}", f"https://d-nb.info/gnd/{gnd}", "Gemeinsame Normdatei"])
    related = []
    if r.get("other_volume"):
        tier, ov, oid, _text, _ev = (r["other_volume"].split("|") + [""] * 5)[:5]
        if oid:
            related.append([ov, tier, oid])
    return links, related


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    geo = streets()
    pages = K.load_pages()
    rows = K.load_rows()  # hängt die Zusatzspalten an die cols in K.TABS an
    labels = {**site_nav.LABELS["de"], **K.LABELS, "page_raw": "Seite im PDF bzw. Bild bei e-rara"}
    recs = []
    for vol in K.VOLUMES:  # wie die Kontrollseite: nur Bände aus 00_volumes.csv
        for key, _label, _fname, cols in K.TABS:
            for row in rows[vol][key]:
                r = dict(zip(cols, row))
                p = pages[vol].get(r.get("page", ""))
                sk, muni = r.get("street_key", ""), r.get("municipality") or "Bern"
                g = (geo.get((muni, sk)) or geo.get(("Bern", sk))) if sk else None
                links, related = links_for(r)
                fields = [(c, r.get(c, "")) for c in cols if c not in CORE]
                if p:
                    fields.insert(0, ("page_raw", r.get("page", "")))
                recs.append({
                    "id": r["entry_id"], "vol": vol, "year": K.baende.jahr(vol), "part": key,
                    "name": r.get("surname", ""), "forename": r.get("forename", ""),
                    "alliance": r.get("alliance_name", ""), "maiden": r.get("maiden_name", ""),
                    "occupation": r.get("occupation_raw", ""), "street": r.get("street_raw", ""),
                    "no": r.get("building_no", ""), "area": "" if muni == "Bern" else muni,
                    "origin": r.get("origin_raw", ""), "title": r.get("title", ""), "heading": r.get("heading", ""),
                    "text": r.get("text", ""), "page": p[1] if p else r.get("page", ""),
                    "page_url": ERARA_PAGE + p[0] if p else "",
                    "lat": g[0] if g else None, "lon": g[1] if g else None,
                    "fields": fields, "links": links, "related": related,
                })
    site_search.build(args.out, city=CITY, records=recs, labels=labels)


if __name__ == "__main__":
    main()
