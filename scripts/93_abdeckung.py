"""93_abdeckung.py — Unterseite «Abdeckung»: die Adressbücher gemessen an BERNHIST (GitHub Pages).

    python scripts/93_abdeckung.py --out _site/abdeckung.html

Liest nur eingecheckte Tabellen: data/abdeckung/abdeckung.csv, sektoren.csv, wachstum.csv
(aus scripts/85_abdeckung.py) und ref/bernhist/werte.csv. Der Bau braucht weder den BERNHIST-Dump noch das Netz.
Methode und Grenzen stehen in docs/abdeckung.md.
"""
from __future__ import annotations

import argparse
import csv
import html
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_nav  # noqa: E402  gemeinsame Navigation
import site_fonts  # noqa: E402  Schriften lokal (fonts/)

DATA = Path("data/abdeckung")
WERTE = Path("ref/bernhist/werte.csv")
REPO_URL = "https://github.com/thodel/adressbuecher-bern"
EXTRA = [("abdeckung", "abdeckung.html", "Abdeckung")]  # weitere Seite der Stadt in der Navigation

# Gruppen der Ergebnistabelle: (Überschrift, Zeilen aus abdeckung.csv)
BLOECKE = [
    ("Stadt und Buch", ["Einträge im Einwohnerverzeichnis", "Personen je Einwohner", "Personen je Haushalt",
                         "Verschiedene Namen", "Firmen", "Ämter, Vereine, Betriebe", "Verweise"]),
    ("Frauen", ["Frauen", "Witwen", "Fräulein", "Frauen mit Erwerb"]),
    ("Erwerb und Sektoren", ["Personen mit Erwerb", "1. Sektor", "2. Sektor", "3. Sektor"]),
    ("Berufsregister", ["Berufsregister: Einheiten", "Berufsregister: im Einwohnerverzeichnis wiedergefunden",
                        "Berufsregister: mit gleicher Adresse wiedergefunden"]),
    ("Gruppen mit eigenem Nenner", [
        "Ärzte (Beruf nennt «Arzt»)", "Ärzte (dazu Titel «Dr. med.»)", "Ärzte (dazu Titel «Dr. med.», gegen Ärztedichte)",
        "Ärzte (Rubrik im Berufsregister)", "Lehrer und Lehrerinnen (öffentliche Schule genannt)",
        "Lehrer und Lehrerinnen (Primarschule genannt)",
        "Lehrer und Lehrerinnen (ohne Fach- und höhere Schulen)", "Lehrer und Lehrerinnen (alle)",
        "Spezereihandlungen (Rubrik im Berufsregister)", "Spezereihandlungen (Einwohnerverzeichnis)",
        "Dienstboten", "Taglöhner und Handlanger"]),
]
NENNER_LABEL = {
    "Personen je Haushalt": "Haushalte", "Frauen": "Frauen in der Stadt", "Witwen": "Witwen", "Frauen mit Erwerb": "erwerbstätige Frauen",
    "Personen mit Erwerb": "Erwerbstätige", "Berufsregister: Einheiten": "Selbständige",
    "Berufsregister: im Einwohnerverzeichnis wiedergefunden": "Zeilen im Register",
    "Berufsregister: mit gleicher Adresse wiedergefunden": "Zeilen im Register",
}

TEMPLATE = r"""<!doctype html>
<html lang="de">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Abdeckung · Adressbücher Bern 1883–1900</title>
<meta name="description" content="Welchen Teil der Stadt Bern bilden die Adressbücher 1883–84 und 1900 ab? Einträge je Einwohner und Haushalt, nach Geschlecht, Sektor und Berufsgruppe, gemessen an BERNHIST.">
<link rel="stylesheet" href="fonts/fonts.css">
<style>
:root {
  --bg: #f6f5f1; --paper: #ffffff; --fg: #1d2129; --muted: #5c6370; --line: #d9d7cf;
  --accent: #7a2e2e; --accent-soft: #f1e3e1; --ok: #2f6f4e; --warn: #9a6b11; --bad: #a33a2a;
  --note-bg: #fbf4e2; --note-line: #e2cf9c; --b1: #b9a48c; --b2: #7a2e2e;
  --font-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --font-data: "Source Code Pro", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #15171b; --paper: #1d2026; --fg: #e8e6df; --muted: #a39f94; --line: #353942;
  --accent: #d08a84; --accent-soft: #3a2626; --ok: #7fc39d; --warn: #d9b35a; --bad: #e08a79;
  --note-bg: #2a2619; --note-line: #5a4d2a; --b1: #7d6f5f; --b2: #d08a84; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #15171b; --paper: #1d2026; --fg: #e8e6df; --muted: #a39f94; --line: #353942;
  --accent: #d08a84; --accent-soft: #3a2626; --ok: #7fc39d; --warn: #d9b35a; --bad: #e08a79;
  --note-bg: #2a2619; --note-line: #5a4d2a; --b1: #7d6f5f; --b2: #d08a84; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font-family: var(--font-body); font-size: 16px; line-height: 1.5;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 16px; margin: 0; }
header { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
main { max-width: 1040px; }
h1 { font-size: 1.45rem; margin: 6px 0 0; font-weight: 700; letter-spacing: -0.01em; text-wrap: balance; }
h2 { font-size: 1.12rem; margin: 30px 0 6px; }
h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin: 0; }
p, li { max-width: 75ch; }
.sub { color: var(--muted); font-size: 0.92rem; margin: 0; }
a { color: var(--accent); }
.note { background: var(--note-bg); border: 1px solid var(--note-line); border-radius: 8px; padding: 8px 12px; font-size: 0.93rem; margin: 14px 0; }
.note p { margin: 0; max-width: none; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; margin: 16px 0 4px; }
.kpi { background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; }
.kpi .v { font-size: 1.5rem; font-weight: 700; font-variant-numeric: tabular-nums; line-height: 1.2; }
.kpi .v small { font-size: 0.85rem; font-weight: 400; color: var(--muted); }
.kpi .l { color: var(--muted); font-size: 0.86rem; }
.wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); margin: 8px 0; }
table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
th, td { text-align: left; padding: 5px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
th { font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); white-space: nowrap; }
td.n .tag { display: block; width: max-content; margin-left: auto; font-family: var(--font-body); }
td.n, th.n { text-align: right; font-family: var(--font-data); font-variant-numeric: tabular-nums; font-size: 0.84rem; white-space: nowrap; }
tr.block td { background: var(--bg); padding-top: 10px; }
td.g { min-width: 16ch; }
td.g small { display: block; color: var(--muted); font-size: 0.8rem; }
td.bars { min-width: 190px; width: 30%; }
.bar { display: grid; grid-template-columns: 4.2em 1fr 4.4em; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--muted); }
.bar .track { height: 9px; background: color-mix(in srgb, var(--line) 55%, transparent); border-radius: 2px; position: relative; }
.bar .fill { position: absolute; inset: 0 auto 0 0; border-radius: 2px; }
.bar.a .fill { background: var(--b1); } .bar.b .fill { background: var(--b2); }
.bar .over { position: absolute; right: -1px; top: -3px; bottom: -3px; width: 2px; background: var(--fg); }
.bar .q { font-family: var(--font-data); color: var(--fg); text-align: right; font-variant-numeric: tabular-nums; }
.legend { color: var(--muted); font-size: 0.84rem; margin: 6px 0; }
.legend i { display: inline-block; width: 12px; height: 9px; border-radius: 2px; margin: 0 4px 0 10px; }
.tag { display: inline-block; border: 1px solid var(--line); border-radius: 4px; padding: 0 5px; font-size: 0.72rem; color: var(--muted); white-space: nowrap; }
details { margin: 8px 0; }
summary { cursor: pointer; color: var(--accent); font-weight: 600; }
footer { color: var(--muted); font-size: 0.82rem; margin-top: 28px; }
@media (max-width: 600px) { body { font-size: 15px; } td.bars { min-width: 150px; } }
__NAVCSS__
</style>
__CITYBAR__
<header>
  __CITYNAV__
  <h1>Wen die Adressbücher erfassen: Abdeckung 1883–84 und 1900</h1>
  <p class="sub">Stand __DATE__ · Einträge der beiden Bände, gemessen an den Zahlen von BERNHIST für die Stadt Bern.</p>
</header>
<main>
<div class="kpis">__KPIS__</div>
<section class="note"><p><b>Wie zu lesen.</b> Ein Adressbuch nennt Erwachsene mit eigener Adresse, Gewerbe und Ämter, keine Köpfe. Der Anteil an den Haushalten sagt deshalb mehr als der Anteil an der Bevölkerung. BERNHIST hat die Berufsstruktur der Stadt nur für 1856 und 1910; die meisten Nenner sind auf das Bandjahr <b>umgerechnet</b> und in der Tabelle so bezeichnet. Die Bände sind maschinell gelesen und nicht korrigiert.</p></section>

<h2>Befund</h2>
<ul>
  <li><b>Rund ein Fünftel der Bevölkerung, aber fast jeder Haushalt.</b> __T_BEV__</li>
  <li><b>Das Buch wächst schneller als die Stadt.</b> __T_WACHSTUM__</li>
  <li><b>Fast vollständig</b> sind 1900 Gruppen mit Gewerbe, Amt oder Praxis: __T_VOLL__</li>
  <li><b>Kaum vorhanden</b> sind Dienstboten und Taglöhner: __T_KAUM__ Wer im Haushalt des Arbeitgebers wohnt oder keinen festen Erwerb hat, steht nicht im Buch.</li>
  <li><b>Frauen</b> stehen vor allem als Witwen oder mit eigenem Erwerb im Buch: __T_FRAUEN__</li>
  <li><b>Der 3. Sektor ist übervertreten, der 2. untervertreten.</b> __T_SEKTOR__</li>
</ul>

<h2>Quoten je Gruppe</h2>
<p class="legend">Anteil des Buchs am Nenner in Prozent <i style="background:var(--b1)"></i>1883–84 <i style="background:var(--b2)"></i>1900 · Balken bis 100 %, darüber mit Strich am Ende. «Buch» ist die Zahl der Einträge, «Nenner» der Wert aus BERNHIST für das Bandjahr.</p>
<div class="wrap"><table>
<thead><tr><th>Gruppe</th><th class="n">Buch 1883–84</th><th class="n">Nenner</th><th class="n">Buch 1900</th><th class="n">Nenner</th><th>Quote</th></tr></thead>
<tbody>__ROWS__</tbody>
</table></div>
<p class="legend">Nenner: <span class="tag">direkt</span> Wert der Volkszählung · <span class="tag">interpoliert</span> linear zwischen zwei Stichjahren · <span class="tag">geschätzt</span> über einen Anteil aus einem anderen Jahr umgerechnet.</p>

<h2>Berufsangaben nach Sektor</h2>
<p>Personen im Einwohnerverzeichnis nach der ersten Berufsangabe, daneben die Erwerbstätigen der Stadt nach BERNHIST. Die Zuordnung geschieht mit Wortlisten; in einer Stichprobe von __TQN__ Berufsangaben waren __TQR__ richtig zugeordnet (__TQP__ %). Die Zahl für den 1. Sektor 1856 ist für eine Stadt nicht plausibel und dient nicht als Nenner.</p>
<div class="wrap"><table>
<thead><tr><th></th><th class="n">1883–84</th><th class="n">Anteil %</th><th class="n">1900</th><th class="n">Anteil %</th><th class="n">BERNHIST 1856 %</th><th class="n">BERNHIST 1910 %</th></tr></thead>
<tbody>__SEKTOREN__</tbody>
</table></div>

<h2>Wachstum 1883 bis 1900</h2>
<div class="wrap"><table>
<thead><tr><th>Grösse</th><th class="n">1883</th><th class="n">1900</th><th class="n">Faktor</th><th class="n">pro Jahr</th></tr></thead>
<tbody>__WACHSTUM__</tbody>
</table></div>

<h2>Grenzen</h2>
<ul>
  <li><b>Haushaltsvorstände statt Köpfe.</b> Die Quote an der Bevölkerung ist eine Untergrenze für die Reichweite des Buchs; Ehefrauen, Kinder und Dienstboten im Haushalt haben keinen eigenen Eintrag.</li>
  <li><b>Nenner aus anderen Jahren.</b> Erwerbstätige, Sektoren, Ärzte, Dienstboten und Taglöhner gibt es in BERNHIST nur für 1856 und 1910. Für den Band 1883–84 überbrückt die Rechnung 27 Jahre.</li>
  <li><b>Nicht dasselbe gezählt.</b> Die 131 Lehrpersonen von 1895 sind mehrheitlich Primarlehrkräfte, die Abgrenzung ist nicht bekannt; «Dr. med.» reicht weiter als «Arzt»; die Dienstboten von 1910 sind anders abgegrenzt als die von 1856. Quoten über 100 % zeigen solche Unterschiede an.</li>
  <li><b>Lesefehler.</b> 84 % und 83 % der Einträge waren in der Stichprobe voll korrekt. Verlesene Berufe fallen zum Teil aus den Gruppen; die Zahl der Frauen ist eine Untergrenze, weil viele Vornamen abgekürzt sind.</li>
</ul>
<p>Methode, Herleitung der Nenner und alle Grenzen: <a href="__REPO__/blob/main/docs/abdeckung.md">docs/abdeckung.md</a>. Tabellen: <a href="__REPO__/tree/main/data/abdeckung">data/abdeckung</a>. Skript: <a href="__REPO__/blob/main/scripts/85_abdeckung.py">scripts/85_abdeckung.py</a>.</p>

<details>
  <summary>Verwendete Werte aus BERNHIST (__NWERTE__)</summary>
  <p class="sub">Einwohnergemeinde Bern (Ort 457). Quelle: BERNHIST, Historisch-statistische Datenbank des Kantons Bern, Dump <code>ub-unibe-ch/bernhist</code> (Stand 22.03.2024). Lizenz: MIT, © 2019 Universität Bern, Universitätsbibliothek (<a href="https://github.com/ub-unibe-ch/bernhist/blob/main/LICENSE">Lizenztext</a>); hier stehen nur die verwendeten Einzelwerte. Zur Datenbank: Christian Pfister, Niklaus Schranz, BERNHIST – Plattform für fächerübergreifendes Forschen und Lehren in Raum und Zeit, Itinera 17 (1995), 46–78.</p>
  <div class="wrap"><table>
  <thead><tr><th>Thema</th><th>Bereich</th><th class="n">Jahr</th><th class="n">Wert</th></tr></thead>
  <tbody>__WERTE__</tbody>
  </table></div>
</details>
</main>
<footer>Zähler: Adressbuch der Stadt Bern 1883–84 und 1900, maschinell gelesen (CC0). Nenner: <a href="https://www.bernhist.ch">BERNHIST</a>, Universitätsbibliothek Bern (MIT-Lizenz). <a href="__REPO__">Daten und Code</a>.</footer>
</html>
"""


def lies(pfad: Path) -> list[dict]:
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def zahl(x: str) -> str:
    if x == "":
        return "–"
    return f"{round(float(x)):,}".replace(",", " ")


def proz(x: str) -> str:
    return "–" if x == "" else f"{float(x):.1f}".replace(".", ",") + " %"


def balken(klasse: str, band: str, q: str) -> str:
    if q == "":
        return f'<div class="bar {klasse}"><span>{band}</span><span></span><span class="q">–</span></div>'
    v = float(q)
    over = '<span class="over"></span>' if v > 100 else ""
    return (f'<div class="bar {klasse}"><span>{band}</span><span class="track"><span class="fill" '
            f'style="width:{min(v, 100):.1f}%"></span>{over}</span><span class="q">{proz(q)}</span></div>')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    rows = {(r["band"], r["gruppe"]): r for r in lies(DATA / "abdeckung.csv")}
    R = lambda band, g: rows[(band, g)]
    A, B = "1883–84", "1900"
    e = html.escape

    trs = []
    for titel, gruppen in BLOECKE:
        trs.append(f'<tr class="block"><td colspan="6"><h3>{e(titel)}</h3></td></tr>')
        for g in gruppen:
            a, b = R(A, g), R(B, g)
            tag = lambda r: f' <span class="tag">{r["nenner_art"]}</span>' if r["nenner_art"] else ""
            nen = NENNER_LABEL.get(g, "")
            klein = "; ".join(x for x in (b["zaehler_was"], b["bemerkung"] or a["bemerkung"]) if x)
            hat = a["quote_prozent"] != "" or b["quote_prozent"] != ""
            trs.append(
                f'<tr><td class="g" title="{e(b["nenner_herleitung"] or a["nenner_herleitung"])}">{e(g)}<small>{e(klein)}</small></td>'
                f'<td class="n">{zahl(a["zaehler"])}</td><td class="n">{zahl(a["nenner"])}{tag(a)}</td>'
                f'<td class="n">{zahl(b["zaehler"])}</td><td class="n">{zahl(b["nenner"])}{tag(b)}</td>'
                f'<td class="bars">{balken("a", A, a["quote_prozent"]) + balken("b", B, b["quote_prozent"]) if hat else ""}'
                f'{f"<small class=legend>Nenner: {e(nen)}</small>" if nen and hat else ""}</td></tr>')

    sek = lies(DATA / "sektoren.csv")
    sek_rows = "".join(
        f'<tr><td>{e(r["zeile"])}</td><td class="n">{zahl(r["n_1883"])}</td><td class="n">{r["anteil_1883"]}</td>'
        f'<td class="n">{zahl(r["n_1900"])}</td><td class="n">{r["anteil_1900"]}</td>'
        f'<td class="n">{r["bernhist_1856"]}</td><td class="n">{r["bernhist_1910"]}</td></tr>' for r in sek)
    wach = lies(DATA / "wachstum.csv")
    W = {r["groesse"]: r for r in wach}
    wach_rows = "".join(
        f'<tr><td>{e(r["groesse"])}</td><td class="n">{zahl(r["wert_1883"])}</td><td class="n">{zahl(r["wert_1900"])}</td>'
        f'<td class="n">{r["faktor"].replace(".", ",")}</td><td class="n">{r["prozent_pro_jahr"].replace(".", ",")} %</td></tr>'
        for r in wach)
    werte = lies(WERTE)
    werte_rows = "".join(
        f'<tr><td>{e(r["thema"])}</td><td>{e(r["thema_pfad"].replace("Alles > ", ""))}</td><td class="n">{r["jahr"]}</td>'
        f'<td class="n">{zahl(r["wert"])}</td></tr>' for r in sorted(werte, key=lambda r: (r["thema_pfad"], r["thema"], r["jahr"])))
    stich = [r for r in lies(DATA / "stichprobe_sektor.csv") if r["soll"]]
    richtig = sum(1 for r in stich if r["soll"] == r["zuordnung"])

    z = lambda band, g: zahl(R(band, g)["zaehler"])
    n = lambda band, g: zahl(R(band, g)["nenner"])
    q = lambda band, g: proz(R(band, g)["quote_prozent"])
    pj = lambda g: W[g]["prozent_pro_jahr"].replace(".", ",") + " %"
    kpis = [
        (q(A, "Personen je Einwohner"), q(B, "Personen je Einwohner"), "Personen im Buch je 100 Einwohner"),
        (q(A, "Personen je Haushalt").replace(" %", ""), q(B, "Personen je Haushalt").replace(" %", ""), "Personen im Buch je 100 Haushalte (geschätzt)"),
        (q(A, "Frauen"), q(B, "Frauen"), "der Frauen in der Stadt"),
        (pj("Personen im Einwohnerverzeichnis"), pj("Wohnbevölkerung (BERNHIST)"), "Wachstum im Jahr: Buch gegen Stadt"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="v">{a} <small>→</small> {b}</div><div class="l">{e(lab)} · 1883–84 → 1900</div></div>'
        for a, b, lab in kpis[:3]) + (
        f'<div class="kpi"><div class="v">{kpis[3][0]} <small>gegen</small> {kpis[3][1]}</div><div class="l">{e(kpis[3][2])}, 1883–1900</div></div>')
    S = {r["zeile"]: r for r in sek}
    texte = {
        "__T_BEV__": f'1883–84 stehen {z(A, "Personen je Einwohner")} Personen im Einwohnerverzeichnis, {q(A, "Personen je Einwohner")} der Wohnbevölkerung ({n(A, "Personen je Einwohner")}, interpoliert) und {q(A, "Personen je Haushalt").replace(chr(160) + "%", "")} je 100 Haushalte. 1900 sind es {z(B, "Personen je Einwohner")} Personen, {q(B, "Personen je Einwohner")} der Bevölkerung ({n(B, "Personen je Einwohner")}) und {q(B, "Personen je Haushalt").replace(chr(160) + "%", "")} je 100 Haushalte.',
        "__T_WACHSTUM__": f'Die Bevölkerung wächst von 1883 bis 1900 um {pj("Wohnbevölkerung (BERNHIST)")} im Jahr, die Zahl der Personen im Einwohnerverzeichnis um {pj("Personen im Einwohnerverzeichnis")}, das Berufsregister um {pj("Einheiten im Berufsregister")} (verschiedene Namen mit Adresse). Der Band 1900 erfasst einen grösseren Teil der Stadt als der Band 1883–84.',
        "__T_VOLL__": f'Ärzte ({z(B, "Ärzte (Beruf nennt «Arzt»)")} mit der Berufsangabe «Arzt» bei {n(B, "Ärzte (dazu Titel «Dr. med.», gegen Ärztedichte)")} bis {n(B, "Ärzte (Beruf nennt «Arzt»)")} erwarteten), Lehrerinnen und Lehrer der Primarschulen ({z(B, "Lehrer und Lehrerinnen (Primarschule genannt)")} bei rund {n(B, "Lehrer und Lehrerinnen (Primarschule genannt)")} Lehrpersonen insgesamt), Spezereihandlungen ({z(B, "Spezereihandlungen (Rubrik im Berufsregister)")} im Berufsregister bei rund {n(B, "Spezereihandlungen (Rubrik im Berufsregister)")}). Der Band 1883–84 liegt überall tiefer.',
        "__T_KAUM__": f'{z(A, "Dienstboten")} und {z(B, "Dienstboten")} Einträge von Dienstboten, {z(A, "Taglöhner und Handlanger")} und {z(B, "Taglöhner und Handlanger")} von Taglöhnern, bei jeweils mehreren Tausend in der Stadt.',
        "__T_FRAUEN__": f'{z(A, "Frauen")} und {z(B, "Frauen")} erkannte Frauen sind {q(A, "Frauen")} und {q(B, "Frauen")} der Frauen in der Stadt; bei den Witwen sind es {q(A, "Witwen")} und {q(B, "Witwen")} (Nenner geschätzt).',
        "__T_SEKTOR__": f'Im Band 1900 gehören {S["3. Sektor"]["anteil_1900"]} % der Personen mit Sektor zum 3. Sektor und {S["2. Sektor"]["anteil_1900"]} % zum 2.; in der Volkszählung 1910 sind es {S["3. Sektor"]["bernhist_1910"]} % und {S["2. Sektor"]["bernhist_1910"]} %. Gemessen an den geschätzten Erwerbstätigen erfasst der Band 1900 {q(B, "3. Sektor")} des 3., {q(B, "2. Sektor")} des 2. und {q(B, "1. Sektor")} des 1. Sektors.',
    }
    page = (TEMPLATE.replace("__CITYBAR__", site_nav.city_bar("bern", "de"))
            .replace("__CITYNAV__", site_nav.city_nav("Bern 1883–1900", REPO_URL, "abdeckung", "de", extra=EXTRA))
            .replace("__NAVCSS__", site_nav.CSS).replace("__KPIS__", kpi_html).replace("__ROWS__", "\n".join(trs))
            .replace("__SEKTOREN__", sek_rows).replace("__WACHSTUM__", wach_rows).replace("__WERTE__", werte_rows)
            .replace("__NWERTE__", str(len(werte))).replace("__TQN__", str(len(stich))).replace("__TQR__", str(richtig))
            .replace("__TQP__", f"{100 * richtig / len(stich):.1f}".replace(".", ","))
            .replace("__REPO__", REPO_URL).replace("__DATE__", date.today().strftime("%d.%m.%Y")))
    for k, v in texte.items():
        page = page.replace(k, v)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    site_fonts.copy(args.out.parent)
    print(f"{len(rows)} Zeilen, {len(werte)} BERNHIST-Werte → {args.out}")


if __name__ == "__main__":
    main()
