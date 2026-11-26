"""be_gemini.py — Strom B (Fraktur 1861–1879) mit Gemini lesen, auf tei (scripts/weekly/README.md).

    python3 be_gemini.py                 # alle Bände von Strom B, aufsteigend (als systemd-Einheit gestartet)
    python3 be_gemini.py --probe 20      # nur die ersten 20 Seiten des ersten Bandes, dann anhalten
    python3 be_gemini.py --status        # Stand, Seiten, Token und Kosten

Liegt neben be_weekly.py in /home/dh/adressbuch_qwen/weekly_bern/ und nimmt von dort Seitentabelle und
Seitenzuordnung (qwen3.8 nennt nur den Teil einer Seite, liest sie nicht). Je Band:
1. Manifest bei e-rara, jede Seite zuordnen; Seitenbereiche Einwohner und Berufe (be_weekly.sections).
2. Jede Seite dieser Bereiche über IIIF holen (Breite des Scans, höchstens 1600 px) und mit Gemini lesen
   (REST generateContent, Denkstufe low, Temperatur 0). Je Seite results/<Band>_p<NNN>.json mit Rohantwort
   und vollständigen usageMetadata (prompt, candidates, thoughts) samt Kosten in $, .jsonl mit den Einträgen
   im Schema von run_qwen.py, damit collect.py sie sammelt.
3. collect.py, Ergebnis auf den Forschungsspeicher (full/bern<Band>/), Seitenbilder werden nicht gespeichert.

Schutz: Nach den ersten 20 gelesenen Seiten und danach laufend gilt: liegen die Kosten im Mittel über
MAX_PER_PAGE oder die Summe über BUDGET, hält der Lauf an (state: «angehalten: …»). Fortsetzbar: gelesene
Seiten werden übersprungen. Den Schlüssel liest der Lauf aus tei's .env.gpustack (GEMINI_API_KEY) und gibt
ihn nie aus; er geht im Kopf x-goog-api-key, nicht in der URL.
"""
from __future__ import annotations

import base64
import csv
import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import be_weekly as bw  # noqa: E402  Seitentabelle, Zuordnung, Seitenbereiche

HERE = bw.HERE
WORK = bw.WORK
SHARE = bw.SHARE
STATE = HERE / "gemini_state.json"
LOG = HERE / "gemini.log"
STREAM = "B"
MODEL = os.environ.get("BE_GEMINI_MODEL", "gemini-3.5-flash")
# Listenpreis gemini-3.5-flash (Stand 26.11.2026, Gemini API): $1.50 je Mio. Eingabe-Token, $9.00 je Mio.
# Ausgabe-Token; Denk-Token zählen als Ausgabe.
PRICE_IN, PRICE_OUT = 1.50 / 1e6, 9.00 / 1e6
MAX_PER_PAGE = 0.08      # $ je Seite im Mittel; darüber hält der Lauf an
BUDGET = 350.0           # $ für Strom B insgesamt; darüber hält der Lauf an
PROBE_PAGES = 20
MAX_WIDTH = 1600
TZ = bw.TZ
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

PROMPT = """Du siehst eine Seite aus einem Adressbuch der Stadt Bern (1861–1879), gesetzt in Fraktur, oft zweispaltig.
Lies die Seite vollständig, Spalte für Spalte (erst die ganze linke, dann die rechte Spalte), und gib JEDEN Eintrag als eine JSON-Zeile aus (JSON Lines, ein Objekt pro Zeile, kein Markdown, kein Kommentar).

Ein Eintrag beginnt mit einem Namen oder einem Gedankenstrich (— = Familienname des vorigen Eintrags wiederholt) und kann über mehrere Druckzeilen laufen (eingerückte Folgezeilen gehören dazu; Trennstriche am Zeilenende auflösen).
Zwischentitel (Buchstaben, Berufsklassen, Strassen, Behörden) gib als eigenes Objekt mit "type":"heading" aus. Kopfzeile/Seitenzahl als "type":"pageheader".

Felder je Eintrag ("type":"entry"):
- "text": der vollständige Eintragstext genau wie gedruckt (Abkürzungen NICHT auflösen, Rechtschreibung der Vorlage, Trennstriche aufgelöst)
- "dash_prefix": true, wenn der Eintrag mit Gedankenstrich beginnt
- "surname": Familienname (bei Gedankenstrich den ergänzten Namen des vorigen Haupteintrags)
- "alliance_name": Allianzname nach Bindestrich (Müller-Hürni -> "Hürni"), sonst ""
- "forename": Vorname(n)/Initialen wie gedruckt
- "title": Dr., Prof., Hr. usw., sonst ""
- "civil_status": Wwe., Wittwe, Frau, Jgfr., geb. ... wie gedruckt, sonst ""
- "occupation": Beruf/Stand wie gedruckt
- "origin": Heimatort, falls angegeben ("von Thun", "v. Biel")
- "street": Strasse/Gasse/Quartier wie gedruckt (bei mehreren Adressen die Wohnadresse)
- "building_no": Hausnummer mit Zusatz (z. B. "92a"), sonst ""
- "phone": "" (es gibt in diesen Jahren kein Telefon)
- "heading": der zuletzt gesehene Zwischentitel, sonst ""

Fraktur: Das lange s (ſ) ist ein s, nie ein f (Haßler, Gysi, Reist; nicht Hafler, Gyfi, Reift); ß bleibt ß; V und B, I und J, k und x, n und u, c und e genau unterscheiden. Die Fraktur-Grossbuchstaben F (𝔉) und J (𝔍) sehen sich ähnlich: F hat oben einen waagrechten Balken und einen Querstrich in der Mitte, J ist unten geschwungen ohne Querstrich; bei Initialen (F., J.) genau hinsehen. Umlaute: ü, ä und ö nach der Form des Grundbuchstabens unterscheiden (Bühler, nicht Bähler); das Verzeichnis ist alphabetisch, ein Name ausserhalb der Reihenfolge ist ein Hinweis auf einen Lesefehler. Schreibweisen nicht modernisieren (Wittwe bleibt Wittwe, Negotiant bleibt Negotiant). Antiqua-Einschübe (Namen, Fremdwörter) wie gedruckt.
Wiederholungszeichen („ oder ") unter einem Wort bedeuten "wie in der Zeile darüber": im Feld "text" das Zeichen stehen lassen, in den Feldern aber den wiederholten Wert einsetzen.
Erfinde nichts. Was nicht lesbar ist, mit [?] markieren. Lass keine Zeile aus. Am Ende eine Zeile {"type":"end","n_entries":<Anzahl>}."""


def log(msg: str) -> None:
    line = f"{dt.datetime.now(TZ):%d.%m %H:%M} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(st: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    tmp.rename(STATE)
    subprocess.run(["rsync", "-t", str(STATE), str(SHARE / "weekly_bern_gemini_state.json")], check=False)


def cost(usage: dict) -> float:
    """$ für eine Antwort aus usageMetadata; Denk-Token sind Ausgabe."""
    out = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
    return round(usage.get("promptTokenCount", 0) * PRICE_IN + out * PRICE_OUT, 6)


def guard(costs: list[float], probe: int = PROBE_PAGES) -> str:
    """Leer, wenn weiterlesen; sonst der Grund zum Anhalten. Geprüft ab der `probe`-ten Seite."""
    if sum(costs) > BUDGET:
        return f"Budget {BUDGET:.0f} $ überschritten ({sum(costs):.2f} $)"
    if len(costs) >= probe and sum(costs) / len(costs) > MAX_PER_PAGE:
        return f"{sum(costs) / len(costs):.3f} $ je Seite über {MAX_PER_PAGE} $"
    return ""


def parse(text: str) -> tuple[list[dict], int]:
    rows, bad = [], 0
    for ln in text.splitlines():
        ln = ln.strip().strip(",")
        if not ln.startswith("{"):
            continue
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            bad += 1
    return rows, bad


def width_of(row: dict) -> int:
    return min(MAX_WIDTH, int(row.get("width") or MAX_WIDTH))


def gemini(jpeg: bytes, key: str) -> dict:
    body = {"contents": [{"role": "user", "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(jpeg).decode()}},
                {"text": PROMPT}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 32000,
                                 "thinkingConfig": {"thinkingLevel": "low"}}}
    req = urllib.request.Request(URL.format(model=MODEL), data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None   # Ablehnung: nicht wiederholen
            if i == 4:
                raise RuntimeError(f"HTTP {e.code} nach 5 Versuchen") from None
        except OSError:
            if i == 4:
                raise
        time.sleep(30 * (i + 1))
    return {}


def read_page(row: dict, vol: str, out: Path, key: str) -> float | None:
    """Eine Seite lesen und ablegen; gibt die Kosten zurück (None: schon gelesen)."""
    stem = f"{vol}_p{int(row['page']):03d}"
    if (out / f"{stem}.json").exists():
        return None
    t0 = time.time()
    resp = gemini(bw.get(f"{row['iiif_image']}/full/{width_of(row)},/0/default.jpg"), key)
    cand = (resp.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
    usage = resp.get("usageMetadata", {})
    rows, bad = parse(text)
    meta = {"image": f"{row['iiif_image']}/full/{width_of(row)},/0/default.jpg", "model": MODEL,
            "model_version": resp.get("modelVersion", ""), "seconds": round(time.time() - t0, 1),
            "finish_reason": cand.get("finishReason"), "ended": bool(rows) and rows[-1].get("type") == "end",
            "bad_lines": bad, "usage": usage, "usd": cost(usage), "content": text}
    (out / f"{stem}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (out / f"{stem}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta["usd"]


def spent(out: Path) -> list[float]:
    return [json.loads(f.read_text())["usd"] for f in sorted(out.glob("*.json"))]


def process(q: dict, st: dict, key: str, limit: int | None) -> bool:
    """Einen Band lesen. False, wenn der Lauf anhalten soll."""
    v = q["volume"]
    vol = f"bern{v}"
    d = HERE / v
    d.mkdir(exist_ok=True)
    s = st.setdefault(v, {"stream": STREAM})
    s.update(status="läuft", started=s.get("started") or f"{dt.datetime.now(TZ):%Y-%m-%d %H:%M}")
    save_state(st)
    rows = bw.pages_table(q, d)
    if "sections" not in s:
        log(f"{v}: Manifest {len(rows)} Seiten; ordne Seiten zu (qwen3.8)")
        s["sections"] = bw.sections(bw.classify(rows, d / "classify.csv"))
        s["pages"] = len(rows)
        save_state(st)
    secs = s["sections"]
    if "einwohner" not in secs:
        s["status"] = "fehler: kein Einwohnerteil erkannt"; save_state(st); log(f"{v}: {s['status']}"); return True
    want = [r for r in rows if any(a <= int(r["page"]) <= b for a, b in secs.values())]
    out = WORK / "full" / vol / "results"
    out.mkdir(parents=True, exist_ok=True)
    todo = [r for r in want if not (out / f"{vol}_p{int(r['page']):03d}.json").exists()]
    if limit is not None:
        todo = todo[:limit]
    log(f"{v}: Teile {secs}, {len(want)} Seiten, offen {len(todo)}")
    all_costs = [c for b in st for c in spent(WORK / "full" / f"bern{b}" / "results")
                 if (WORK / "full" / f"bern{b}" / "results").exists()]
    stop = ""
    with ThreadPoolExecutor(4) as ex:
        for i in range(0, len(todo), 8):          # in Achterschritten, damit der Schutz früh greift
            for c in ex.map(lambda r: read_page(r, vol, out, key), todo[i:i + 8]):
                if c is not None:
                    all_costs.append(c)
            stop = guard(all_costs)
            if stop:
                break
    c = spent(out)
    s.update(read=len(c), usd=round(sum(c), 2))
    if stop:
        s["status"] = f"angehalten: {stop}"; save_state(st); log(f"{v}: {s['status']}"); return False
    if limit is not None:
        s["status"] = "probe"; save_state(st); log(f"{v}: Probe, {len(c)} Seiten, {sum(c):.2f} $"); return False
    retry = [r for r in want if '"ended": true' not in
             (out / f"{vol}_p{int(r['page']):03d}.json").read_text()]
    s["not_ended"] = [int(r["page"]) for r in retry]
    subprocess.run([sys.executable, "collect.py", str(out), "--volume", vol, "--out", str(out.parent / "entries.csv")],
                   cwd=WORK, stdout=open(d / "run.log", "a"), stderr=subprocess.STDOUT)
    n = sum(1 for _ in open(out.parent / "entries.csv", encoding="utf-8")) - 1 if (out.parent / "entries.csv").exists() else 0
    subprocess.run(["rsync", "-rt", f"{out.parent}/", str(SHARE / "full" / vol) + "/"], check=False)
    subprocess.run(["rsync", "-rt", f"{d}/", str(SHARE / "weekly_bern" / v) + "/"], check=False)
    s.update(status="gelesen", entries=n, finished=f"{dt.datetime.now(TZ):%Y-%m-%d %H:%M}")
    save_state(st)
    log(f"{v}: gelesen, {n} Einträge, {len(c)} Seiten, {sum(c):.2f} $, ohne Ende: {s['not_ended']}")
    return True


def clean_key(raw: str) -> str:
    """Der Schlüssel ohne Anführungszeichen, Leer- und Steuerzeichen (in .env.gpustack stehen welche dahinter;
    mit ihnen lehnt die API ab). Nie ausgeben."""
    m = re.search(r"[A-Za-z0-9._-]{20,}", raw or "")
    return m.group(0) if m else ""


def load_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    f = Path("/home/dh/agentic_historian/.env.gpustack")
    if not key and f.exists():
        for line in f.read_text().splitlines():
            k, sep, val = line.partition("=")
            if sep and k.strip() == "GEMINI_API_KEY":
                key = val
    return clean_key(key)


def main() -> None:
    st = load_state()
    if "--status" in sys.argv:
        for v, s in st.items():
            print(v, s.get("status"), s.get("read", ""), f"{s.get('usd', '')} $", s.get("entries", ""), s.get("sections", ""))
        print(f"zusammen {sum(s.get('usd', 0) for s in st.values()):.2f} $")
        return
    limit = int(sys.argv[sys.argv.index("--probe") + 1]) if "--probe" in sys.argv else None
    bw.load_env()                                 # GPUSTACK_* für die Seitenzuordnung
    key = load_key()
    if not key:
        log("kein GEMINI_API_KEY"); return
    lock = open(HERE / ".gemini.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return
    queue = [q for q in csv.DictReader(open(HERE / "queue.csv", encoding="utf-8")) if q["stream"] == STREAM]
    for q in queue:
        s = st.get(q["volume"], {})
        if s.get("status") == "gelesen" or str(s.get("status", "")).startswith("fehler"):
            continue
        if str(s.get("status", "")).startswith("angehalten") and "--resume" not in sys.argv:
            log(f"{q['volume']}: angehalten, weiter nur mit --resume"); return
        try:
            if not process(q, st, key, limit):
                return
        except Exception as e:
            st.setdefault(q["volume"], {})["status"] = f"fehler: {type(e).__name__}: {str(e)[:120]}"
            save_state(st); log(f"{q['volume']}: {e!r}"[:300])
            return                                 # ein Fehler beim Lesen hält den Lauf an, statt Geld zu verbrennen
    log("Strom B fertig")


if __name__ == "__main__":
    main()
