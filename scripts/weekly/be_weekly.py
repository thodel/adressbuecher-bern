"""be_weekly.py — Lesen der fehlenden Berner Bände auf tei, Strom A (scripts/weekly/README.md).

    python3 be_weekly.py            # vom cron stündlich gestartet (crontab.txt)
    python3 be_weekly.py --status   # Stand ausgeben
    python3 be_weekly.py --only 1881   # nur diesen Band (Probe), auch wenn Zürich liest

Liegt auf tei in /home/dh/adressbuch_qwen/weekly_bern/ neben queue.csv; run_qwen.py und collect.py
liegen eine Ebene höher. Der Lauf nimmt die Bände von Strom A (Antiqua, qwen3.8) in der Reihenfolge von
queue.csv, einen nach dem anderen. Strom B (Fraktur) liest Gemini, nicht dieser Lauf.

Er beginnt erst, wenn sonst nichts liest: kein run_qwen.py und kein zh_weekly.py (das Zürcher Fenster
1900–1920 hat Vorrang). Ein Sperrfile verhindert zwei Läufe gleichzeitig. Je Band:
1. Manifest bei e-rara holen, Seitentabelle schreiben (<Band>/iiif_pages.csv).
2. Jede Seite zuordnen (Bild 600 px breit, qwen3.8 nennt den Teil). Der grösste zusammenhängende Block
   ergibt die Seitenbereiche Einwohner und Berufe.
3. Die Seiten beider Teile über IIIF holen (halbe Breite des Scans, 1100–1200 px), mit run_qwen.py lesen
   (2× vergrössert, zwei Durchgänge), mit collect.py sammeln.
4. Ergebnis auf den Forschungsspeicher (/mnt/wbkolleg_dh_1/tei/adressbuch_qwen/full/bern<Band>/),
   Seitenbilder löschen; sie sind über IIIF jederzeit wieder holbar. Kein Schlüssel wird ausgegeben.
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
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent          # /home/dh/adressbuch_qwen/weekly_bern
WORK = HERE.parent                              # /home/dh/adressbuch_qwen (run_qwen.py, collect.py)
SHARE = Path("/mnt/wbkolleg_dh_1/tei/adressbuch_qwen")
STATE = HERE / "state.json"
LOG = HERE / "weekly.log"
STREAM = "A"
UA = {"User-Agent": "adressbuecher-bern (Universitaet Bern, DH)"}
TZ = dt.timezone(dt.timedelta(hours=1))         # MEZ
OTHERS = "run_qwen.py|zh_weekly.py"             # solange einer davon läuft, wartet Bern
PARTS = ("einwohner", "berufe", "haeuser", "strassen", "behoerden", "inserate", "andere")
PROMPT = """Du siehst eine Seite aus einem Adressbuch der Stadt Bern (1881–1914). Antworte NUR mit einem
JSON-Objekt, ohne Markdown: {"teil": "..."}.
teil, genau eines von:
- "einwohner": alphabetisches Verzeichnis der Einwohner und Firmen (Familienname, Vorname, Beruf, Adresse)
- "berufe": Verzeichnis nach Berufen, Gewerben oder Branchen (Zwischentitel sind Berufe, darunter Namen mit Adresse)
- "haeuser": Verzeichnis nach Strassen und Hausnummern (Eigentümer, Bewohner je Haus)
- "strassen": Strassenverzeichnis (nur Strassennamen, Quartiere, Lage)
- "behoerden": Behörden, Ämter, Vereine, Institutionen, Kirchen, Schulen, Tarife, Kalender
- "inserate": ganzseitige Anzeigen oder Reklame
- "andere": Titelblatt, Inhaltsverzeichnis, leere Seite, Karte, Vorwort"""


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
    subprocess.run(["rsync", "-t", str(STATE), str(SHARE / "weekly_bern_state.json")], check=False)


def busy() -> bool:
    """Liest gerade etwas anderes (ein Lesedurchgang oder der Zürcher Lauf)?"""
    r = subprocess.run(["pgrep", "-f", OTHERS], capture_output=True, text=True)
    return bool(r.stdout.strip())


def next_volume(queue: list[dict], st: dict, only: str | None = None) -> dict | None:
    """Der nächste Band von Strom A, der noch keinen Stand hat, in der Reihenfolge von queue.csv."""
    for q in queue:
        if only and q["volume"] != only:
            continue
        if q["stream"] == STREAM and q["volume"] not in st:
            return q
    return None


def canvases(manifest: dict) -> list[dict]:
    rows = []
    for n, c in enumerate(manifest["sequences"][0]["canvases"], 1):
        rows.append({"page": n, "label": c.get("label", ""), "canvas": c["@id"],
                     "iiif_image": c["images"][0]["resource"]["service"]["@id"], "width": c.get("width", 0)})
    return rows


def pages_table(q: dict, d: Path) -> list[dict]:
    with urllib.request.urlopen(urllib.request.Request(q["manifest"], headers=UA), timeout=120) as r:
        rows = [{"volume": q["volume"], **c} for c in canvases(json.loads(r.read()))]
    with open(d / "iiif_pages.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    return rows


def sections(rows: list[dict]) -> dict:
    """Seitenbereiche aus der Zuordnung: der grösste Block je Teil (Lücken bis 8 Seiten, etwa eingestreute
    Inserate, gehören dazu), mindestens 5 Seiten. Berufe beginnen nie vor dem Ende der Einwohner."""
    out = {}
    for part in ("einwohner", "berufe"):
        ps = sorted(int(r["page"]) for r in rows if r["part"] == part)
        blocks, cur = [], []
        for p in ps:
            if cur and p - cur[-1] > 8:
                blocks.append(cur); cur = []
            cur.append(p)
        if cur:
            blocks.append(cur)
        best = max(blocks, key=len, default=[])
        if len(best) >= 5:
            out[part] = [best[0], best[-1]]
    if "einwohner" in out and "berufe" in out and out["berufe"][0] <= out["einwohner"][1]:
        out["berufe"][0] = out["einwohner"][1] + 1
        if out["berufe"][0] > out["berufe"][1]:
            del out["berufe"]
    return out


def read_width(rows: list[dict]) -> int:
    """Halbe Breite des Scans, aber 1100–1200 px. Probe 1881 S. 120 (25.11.2026): von 13 Einträgen, die
    800 und 1100 px verschieden lasen, war 1100 px fünfmal richtig, 800 px zweimal."""
    return max(1100, min(1200, round(int(rows[len(rows) // 2]["width"] or 2000) / 2)))


def get(url: str) -> bytes:
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except OSError:
            if i == 4:
                raise
            time.sleep(10 * (i + 1))
    return b""


def ask(b64: str) -> str:
    base = os.environ["GPUSTACK_BASE_URL"].rstrip("/")
    body = {"model": os.environ.get("BE_MODEL", "qwen3.8-27b"), "temperature": 0, "max_tokens": 40,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": PROMPT}]}]}
    req = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['GPUSTACK_API_KEY']}",
                                          "Content-Type": "application/json"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                text = json.loads(r.read())["choices"][0]["message"].get("content") or ""
            m = re.search(r"\{.*\}", text, re.S)
            part = (json.loads(m.group()) if m else {}).get("teil", "")
            return part if part in PARTS else "andere"
        except (OSError, ValueError):
            if i == 3:
                return ""
            time.sleep(30 * (i + 1))
    return ""


def classify(rows: list[dict], out: Path) -> list[dict]:
    """Jede Seite einem Teil zuordnen; fortsetzbar (schon zugeordnete Seiten bleiben)."""
    done = {}
    if out.exists():
        done = {int(r["page"]): r for r in csv.DictReader(open(out, encoding="utf-8")) if r["part"]}
    todo = [r for r in rows if int(r["page"]) not in done]

    def one(r: dict) -> dict:
        b64 = base64.b64encode(get(f"{r['iiif_image']}/full/600,/0/default.jpg")).decode()
        return {"page": int(r["page"]), "label": r["label"], "part": ask(b64)}

    with ThreadPoolExecutor(4) as ex:
        for res in ex.map(one, todo):
            done[res["page"]] = res
    res = sorted(done.values(), key=lambda r: int(r["page"]))
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["page", "label", "part"])
        w.writeheader(); w.writerows(res)
    return res


def fetch(rows: list[dict], ranges: list[list[int]], width: int, vol: str, dest: Path) -> None:
    """Seitenbilder über IIIF holen, nacheinander mit kurzer Pause; vorhandene bleiben."""
    dest.mkdir(parents=True, exist_ok=True)
    svc = {int(r["page"]): r["iiif_image"] for r in rows}
    for lo, hi in ranges:
        for p in range(lo, hi + 1):
            f = dest / f"{vol}_p{p:03d}.jpeg"
            if f.exists() and f.stat().st_size > 10000:
                continue
            tmp = f.with_suffix(".part")
            tmp.write_bytes(get(f"{svc[p]}/full/{width},/0/default.jpg"))
            tmp.rename(f)
            time.sleep(0.3)


def run(cmd: list[str], logfile: Path) -> int:
    with open(logfile, "a") as f:
        return subprocess.run(cmd, cwd=WORK, stdout=f, stderr=subprocess.STDOUT).returncode


def process(q: dict, st: dict) -> None:
    v = q["volume"]
    vol = f"bern{v}"
    d = HERE / v
    d.mkdir(exist_ok=True)
    s = st.setdefault(v, {"stream": q["stream"]})
    s.update(status="läuft", started=f"{dt.datetime.now(TZ):%Y-%m-%d %H:%M}")
    save_state(st)
    rows = pages_table(q, d)
    log(f"{v}: Manifest {len(rows)} Seiten; ordne Seiten zu")
    secs = sections(classify(rows, d / "classify.csv"))
    s.update(sections=secs, pages=len(rows))
    if "einwohner" not in secs:
        s["status"] = "fehler: kein Einwohnerteil erkannt"; save_state(st); log(f"{v}: {s['status']}"); return
    width = read_width(rows)
    out = WORK / "full" / vol
    (out / "results").mkdir(parents=True, exist_ok=True)
    log(f"{v}: Teile {secs}, hole Bilder ({width} px)")
    fetch(rows, list(secs.values()), width, vol, out / "pages")
    for p in (1, 2):
        todo = [str(f) for f in sorted((out / "pages").glob("*.jpeg"))
                if '"ended": true' not in ((out / "results" / f"{f.stem}_x2.json").read_text()
                                            if (out / "results" / f"{f.stem}_x2.json").exists() else "")]
        log(f"{v}: Durchgang {p}, {len(todo)} Seiten")
        if todo:
            run([sys.executable, "run_qwen.py", "--workers", "4", "--upscale", "2", "--out", str(out / "results"), *todo],
                out / "run.log")
    run([sys.executable, "collect.py", str(out / "results"), "--volume", vol, "--out", str(out / "entries.csv")], d / "run.log")
    n = sum(1 for _ in open(out / "entries.csv", encoding="utf-8")) - 1 if (out / "entries.csv").exists() else 0
    subprocess.run(["rsync", "-rt", "--exclude", "pages/", f"{out}/", str(SHARE / "full" / vol) + "/"], check=False)
    subprocess.run(["rsync", "-rt", f"{d}/", str(SHARE / "weekly_bern" / v) + "/"], check=False)
    subprocess.run(["rm", "-rf", str(out / "pages")], check=False)
    s.update(status="gelesen", entries=n, finished=f"{dt.datetime.now(TZ):%Y-%m-%d %H:%M}", width=width)
    save_state(st)
    log(f"{v}: gelesen, {n} Einträge; Bilder gelöscht")


def load_env() -> None:
    """GPUSTACK_* aus tei's .env.gpustack lesen (Zeilen, an denen `sh` scheitert). Werte nie ausgeben."""
    f = Path("/home/dh/agentic_historian/.env.gpustack")
    if "GPUSTACK_API_KEY" in os.environ or not f.exists():
        return
    for line in f.read_text().splitlines():
        k, sep, val = line.partition("=")
        if sep and k.startswith("GPUSTACK_"):
            os.environ[k] = val.strip().strip('"').strip("'")


def transient(e: BaseException) -> bool:
    """Server- oder Netzfehler, nach denen der Band nicht als fehlerhaft gilt: HTTP 5xx, 429, Zeitüberschreitung,
    keine Verbindung. Der Lauf endet; cron startet ihn zur nächsten Stunde wieder."""
    import socket
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        return e.code >= 500 or e.code == 429
    return isinstance(e, (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError))


def main() -> None:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    st = load_state()
    if "--status" in sys.argv:
        for v, s in st.items():
            print(v, s.get("stream"), s.get("status"), s.get("entries", ""), s.get("sections", ""))
        return
    load_env()
    lock = open(HERE / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return
    queue = list(csv.DictReader(open(HERE / "queue.csv", encoding="utf-8")))
    for v in [v for v, s in st.items() if s.get("status") == "läuft"]:
        log(f"{v}: abgebrochener Lauf, nehme den Band wieder auf")   # run_qwen.py überspringt fertige Seiten
        del st[v]
    while True:
        if not only and busy():
            log("anderer Lesedurchgang aktiv, warte"); return
        free = os.statvfs("/").f_bavail * os.statvfs("/").f_frsize / 1e9
        if free < 3:
            log(f"nur {free:.1f} GB frei auf /, warte"); return
        nxt = next_volume(queue, st, only)
        if not nxt:
            return
        try:
            process(nxt, st)
        except Exception as e:
            if transient(e):   # GPUStack/e-rara kurz weg (27.11.2026: 504/500 für alle 23 Bände in drei Minuten)
                st.pop(nxt["volume"], None); save_state(st)
                log(f"{nxt['volume']}: {e!r}; Server nicht erreichbar, nächster Versuch mit dem nächsten Lauf"); return
            st.setdefault(nxt["volume"], {})["status"] = f"fehler: {type(e).__name__}"
            save_state(st); log(f"{nxt['volume']}: {e!r}")
        if only:
            return


if __name__ == "__main__":
    main()
