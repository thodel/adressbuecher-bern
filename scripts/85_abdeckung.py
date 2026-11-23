"""85_abdeckung.py — Abdeckung der Adressbücher 1883–84 und 1900, gemessen an BERNHIST.

    python scripts/85_abdeckung.py                       # rechnet mit ref/bernhist/werte.csv
    python scripts/85_abdeckung.py --bernhist <sqlite>   # liest die Werte zuerst neu aus dem Dump
    BERNHIST_SQLITE=<sqlite> python scripts/85_abdeckung.py
    python scripts/85_abdeckung.py --stichprobe 40       # zieht die Stichprobe zur Sektorzuordnung neu

Nenner: BERNHIST (Historisch-statistische Datenbank des Kantons Bern, Stadt Bern = Ort 457). Im Repo liegen
nur die verwendeten Einzelwerte (ref/bernhist/werte.csv), nicht der Dump. Zähler: data/csv/04_entries.csv
und 04_berufe.csv. Ergebnis: data/abdeckung/abdeckung.csv, data/abdeckung/sektoren.csv und der
Tabellenblock in docs/abdeckung.md (zwischen den Marken TABELLEN:START und TABELLEN:ENDE).

Was gezählt wird und warum, steht in docs/abdeckung.md.
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"
OUT_DIR = ROOT / "data" / "abdeckung"
WERTE = ROOT / "ref" / "bernhist" / "werte.csv"
STICHPROBE = OUT_DIR / "stichprobe_sektor.csv"
DOC = ROOT / "docs" / "abdeckung.md"
ORT = 457  # Einwohnergemeinde Bern
QUELLE = "BERNHIST, Dump ub-unibe-ch/bernhist (Stand 22.03.2024)"

# Redaktionsjahr je Band: Der Band 1883–84 erschien 1883; die Volkszählungen waren am 1. Dezember.
JAHR = {"1883": 1883, "1900": 1900}
BAND = {"1883": "1883–84", "1900": "1900"}

# ── Verwendete BERNHIST-Werte: Schlüssel → (Thema, Jahr, Rang) ────────────────────────────────────────
# Rang wählt bei doppelten Werten (1856 und 1910 gibt es zwei Zählungen der Erwerbstätigen) den n-ten
# nach aufsteigender data_entry.id. 1910 gibt es zwei Reihen: Rang 0 (35 250) im Gebietsstand von 1910, mit dem
# 1. und 2. Sektor und Frauen/Männern; Rang 1 (37 247) mit allen drei Sektoren, aber mit Bümpliz (eingemeindet
# 1919), während die Bevölkerung 1910 (85 651) ohne Bümpliz zählt. Verwendet wird Rang 0, der 3. Sektor ist der
# Rest (werte_laden). Bis 23.11.2026 stand hier Rang 1; gefunden in vernetzte-schweiz, docs/durchdringung_bern.md.
ABFRAGE = {
    "bev_1856": (990, 1856, 0), "bev_1880": (990, 1880, 0), "bev_1888": (990, 1888, 0),
    "bev_1900": (990, 1900, 0), "bev_1910": (990, 1910, 0), "bev_1930": (990, 1930, 0),
    "haushalte_1860": (543, 1860, 0), "haushalte_1888": (543, 1888, 0), "bev_1860": (990, 1860, 0),
    "frauen_1856": (362, 1856, 0), "maenner_1856": (696, 1856, 0),
    "frauen_1930": (362, 1930, 0), "maenner_1930": (696, 1930, 0),
    "verwitwet_1856": (988, 1856, 0), "verwitwet_1910": (988, 1910, 0),
    "ledig_1856": (984, 1856, 0), "ledig_1910": (984, 1910, 0),
    "verheiratet_1856": (986, 1856, 0), "verheiratet_1910": (986, 1910, 0),
    "geschieden_1856": (982, 1856, 0), "geschieden_1910": (982, 1910, 0),
    "witwen_1846": (360, 1846, 0), "witwer_1846": (694, 1846, 0),
    "erw_1856": (342, 1856, 1), "erw_s1_1856": (305, 1856, 0), "erw_s2_1856": (314, 1856, 0),
    "erw_s3_1856": (327, 1856, 0), "erw_1856_stellung": (342, 1856, 0),
    "selbstaendige_1856": (341, 1856, 0), "selbstaendige_1930": (341, 1930, 0),
    "dienstboten_1856": (344, 1856, 0), "dienstboten_1910": (344, 1910, 0), "tagloehner_1856": (347, 1856, 0),
    "erw_1910": (342, 1910, 0), "erw_s1_1910": (305, 1910, 0), "erw_s2_1910": (314, 1910, 0),
    "erw_frauen_1910": (345, 1910, 0), "erw_maenner_1910": (346, 1910, 0),
    "aerzte_1856": (1713, 1856, 0), "aerzte_1910": (1713, 1910, 0),
    "lehrpersonen_1895": (1745, 1895, 0), "schueler_1895": (1701, 1895, 0),
    "spezerei_1901": (1690, 1901, 0), "spezerei_1909": (1690, 1909, 0),
}
WERTE_FELDER = ["schluessel", "ort_id", "ort", "thema_id", "thema", "thema_pfad", "jahr", "wert",
                "data_entry_id", "quelle"]


def werte_aus_dump(pfad: Path) -> list[dict]:
    """Liest die in ABFRAGE genannten Einzelwerte aus dem lokal geladenen BERNHIST-Dump."""
    db = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
    ort = db.execute("select name from location where id=?", (ORT,)).fetchone()[0]
    themen = {i: (p, n) for i, p, n in db.execute("select id, parent_id, name from topic")}

    def pfad_von(tid: int) -> str:
        teile = []
        while tid in themen and themen[tid][0]:
            tid = themen[tid][0]
            teile.append(themen[tid][1])
        return " > ".join(reversed(teile))

    out = []
    for key, (tid, jahr, rang) in sorted(ABFRAGE.items()):
        rows = db.execute("select id, value from data_entry where location_id=? and topic_id=? and year_from=? "
                          "and year_to=? order by id", (ORT, tid, jahr, jahr)).fetchall()
        if len(rows) <= rang:
            raise SystemExit(f"BERNHIST: kein Wert für {key} (Thema {tid}, {jahr})")
        did, val = rows[rang]
        out.append({"schluessel": key, "ort_id": ORT, "ort": ort, "thema_id": tid, "thema": themen[tid][1],
                    "thema_pfad": pfad_von(tid), "jahr": jahr, "wert": f"{val:g}", "data_entry_id": did,
                    "quelle": QUELLE})
    return out


def lies(pfad: Path) -> list[dict]:
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def werte_laden(pfad: Path = WERTE) -> dict[str, float]:
    w = {r["schluessel"]: float(r["wert"]) for r in lies(pfad)}
    w["erw_s3_1910"] = w["erw_1910"] - w["erw_s1_1910"] - w["erw_s2_1910"]   # Reihe 1910 ohne 3. Sektor: Rest
    return w


# ── Rechenlogik ──────────────────────────────────────────────────────────────────────────────────────
def interpoliere(j0: float, w0: float, j1: float, w1: float, j: float) -> float:
    """Linear zwischen zwei Stichjahren; ausserhalb wird nicht extrapoliert."""
    if not min(j0, j1) <= j <= max(j0, j1):
        raise ValueError(f"{j} liegt nicht zwischen {j0} und {j1}")
    return w0 if j0 == j1 else w0 + (w1 - w0) * (j - j0) / (j1 - j0)


def quote(zaehler: float, nenner: float) -> float:
    """Anteil in Prozent, auf eine Stelle."""
    return round(100 * zaehler / nenner, 1)


def jahresrate(w0: float, w1: float, jahre: float) -> float:
    """Mittleres jährliches Wachstum in Prozent."""
    return round(100 * ((w1 / w0) ** (1 / jahre) - 1), 2)


def nenner(w: dict[str, float], band: str) -> dict[str, tuple[float, str, str]]:
    """Nenner je Band: Name → (Wert, Art, Herleitung). Art: direkt, interpoliert oder geschätzt."""
    j = JAHR[band]
    if j == 1900:
        bev = (w["bev_1900"], "direkt", "Volkszählung 1900")
    else:
        bev = (interpoliere(1880, w["bev_1880"], 1888, w["bev_1888"], j), "interpoliert",
               f"Volkszählungen 1880 und 1888, linear auf {j}")
    b = bev[0]
    hg = w["bev_1888"] / w["haushalte_1888"]
    erw_q = interpoliere(1856, w["erw_1856"] / w["bev_1856"], 1910, w["erw_1910"] / w["bev_1910"], j)
    erw = b * erw_q
    n = {
        "bevoelkerung": bev,
        "haushalte": (b / hg, "geschätzt", f"Bevölkerung {j} durch die Haushaltsgrösse von 1888 ({hg:.2f} Personen)"),
        "erwerbstaetige": (erw, "geschätzt", f"Bevölkerung {j} mal Erwerbsquote, zwischen 1856 und 1910 interpoliert ({100 * erw_q:.1f} %)"),
        "frauen": (b * interpoliere(1856, w["frauen_1856"] / w["bev_1856"], 1930, w["frauen_1930"] / w["bev_1930"], j),
                   "geschätzt", "Bevölkerung mal Frauenanteil, zwischen 1856 und 1930 interpoliert"),
        "erwerbstaetige_frauen": (erw * w["erw_frauen_1910"] / (w["erw_frauen_1910"] + w["erw_maenner_1910"]),
                                  "geschätzt", "geschätzte Erwerbstätige mal Frauenanteil der Erwerbstätigen 1910"),
        "selbstaendige": (b * interpoliere(1856, w["selbstaendige_1856"] / w["bev_1856"], 1930,
                                           w["selbstaendige_1930"] / w["bev_1930"], j),
                          "geschätzt", "Bevölkerung mal Anteil der Selbständigen, zwischen 1856 und 1930 interpoliert"),
        "dienstboten": (b * w["dienstboten_1856"] / w["bev_1856"], "geschätzt",
                        "Bevölkerung mal Anteil der Dienstboten 1856 (der Wert von 1910 ist anders abgegrenzt)"),
        "tagloehner": (b * w["tagloehner_1856"] / w["bev_1856"], "geschätzt",
                       "Bevölkerung mal Anteil der Taglöhner 1856 (kein späterer Wert)"),
        "aerzte_linear": (interpoliere(1856, w["aerzte_1856"], 1910, w["aerzte_1910"], j), "interpoliert",
                          "Zahl der Ärzte 1856 und 1910, linear"),
        "aerzte_dichte": (b * interpoliere(1856, w["aerzte_1856"] / w["bev_1856"], 1910,
                                           w["aerzte_1910"] / w["bev_1910"], j),
                          "geschätzt", "Bevölkerung mal Ärztedichte, zwischen 1856 und 1910 interpoliert"),
    }
    verw = interpoliere(1856, w["verwitwet_1856"] / w["bev_1856"], 1910, w["verwitwet_1910"] / w["bev_1910"], j)
    n["verwitwete"] = (b * verw, "geschätzt", "Bevölkerung mal Anteil der Verwitweten, zwischen 1856 und 1910 interpoliert")
    n["witwen"] = (b * verw * w["witwen_1846"] / (w["witwen_1846"] + w["witwer_1846"]), "geschätzt",
                   "geschätzte Verwitwete mal Frauenanteil der Verwitweten 1846 (einziges Jahr mit Zivilstand nach Geschlecht)")
    for s in "123":
        n[f"sektor{s}"] = (erw * w[f"erw_s{s}_1910"] / w["erw_1910"], "geschätzt",
                           f"geschätzte Erwerbstätige mal Anteil des {s}. Sektors 1910")
    b1895 = interpoliere(1888, w["bev_1888"], 1900, w["bev_1900"], 1895)
    n["lehrpersonen"] = (b * w["lehrpersonen_1895"] / b1895, "geschätzt",
                         "Lehrer und Lehrerinnen 1895, mit der Bevölkerung auf das Bandjahr umgerechnet")
    b1901 = interpoliere(1900, w["bev_1900"], 1910, w["bev_1910"], 1901)
    n["spezerei"] = (b * w["spezerei_1901"] / b1901, "geschätzt",
                     "Spezerei- und Kolonialwarengeschäfte 1901, mit der Bevölkerung auf das Bandjahr umgerechnet")
    return n


# ── Zähler: Art des Eintrags ─────────────────────────────────────────────────────────────────────────
# `entry_type` in den CSV trifft auch Personen (das Muster sieht «Gesellschaftsstrasse» und «Waffenfabrik»);
# hier wird die Art deshalb nur aus den Namensfeldern bestimmt.
VERWEIS = re.compile(r"\bs\. ?(?:auch|a\.)|\bsiehe\b|\(s\. ", re.I)
FIRMA = re.compile(r"&|\bCie\b|\bComp\b|\bCo\b\.?|\bGebr(?:\b|ü)|\bSöhne\b|\bErben\b|\bfrères\b|A\.-?G\.|"
                   r"Aktiengesellschaft", re.I)
INSTITUTION = re.compile(
    r"gesellschaft|verein|genossenschaft|gemeinde|anstalt|bank\b|kasse\b|fabrik|bureau|büro|direktion|"
    r"verwaltung|schule\b|schulen\b|schulhaus|spital|klinik|kirche|kapelle|hotel|hôtel|museum|bahnhof|"
    r"\bpost\b|amt\b|kanzlei|inspektorat|station|halle\b|heimat\b|asyl|waisenhaus|zunfthaus|amthaus|rathaus|"
    r"gasthaus|gasthof|kornhaus|zeughaus|vereinshaus|departement|kommission|komite|redaktion|bibliothek|theater|"
    r"kaserne|depot|magazin|\bzunft|gericht|polizei|konsulat|gesandtschaft|seminar|gymnasium|universität|"
    r"hochschule|institut|stiftung|korps|feuerwehr|instruktor|kommando|friedhof|brauerei|druckerei|handlung|"
    r"agentur|expedition|zeitung|blatt\b|archiv|wesen\b|schweiz\.|eidg|\bkant\.|\bstädt|\bau\b|\bzum\b|\bzur\b", re.I)


def art(r: dict) -> str:
    """person, firma (Personenfirma), institution (Amt, Verein, Betrieb ohne Personenname) oder verweis."""
    if VERWEIS.search(r["text"]) and not r["building_no"]:
        return "verweis"
    geerbt = (r["dash_prefix"] == "1" and FIRMA.search(r["surname"]) and r["forename"]
              and not FIRMA.search(r["forename"]))  # «— Lina» unter «Jäggi & Cie.»: eine Person
    kopf = re.split(r"[,(]", r["text"])[0]  # «— & Comp., Banquiers»: die Marke steht nur im Text
    if (FIRMA.search(f"{r['surname']} {r['forename']}") and not geerbt) or (not r["forename"] and FIRMA.search(kopf)):
        return "firma"
    if not r["forename"] and not r["civil_status"] and not r["alliance_name"] and (
            INSTITUTION.search(r["surname"]) or len(r["surname"].split()) >= 3):
        return "institution"
    return "person"


# ── Zähler: Frauen ───────────────────────────────────────────────────────────────────────────────────
WITWE = re.compile(r"\bWwe\b|\bWit+we\b|\bveuve\b|\bVve\b", re.I)
FRAEULEIN = re.compile(r"\bFrl\b|\bFräul|\bJgfr\b|\bjgr\b|\bJungfer|\bMlle\b|\bMesdemoiselles\b|\bSchw(?:\b|est)|\bGeschw", re.I)
FRAU = re.compile(r"\bFrau(?:en)?\b|\bMme\b|\bMad\b|\bgeb\.", re.I)
WEIBL_BERUF = re.compile(r"^(?:gew\. )?[\w.\- ]*?(?:erin|rinnen|istin|lerin|frau|tochter|magd|amme|ière|ières|iére|"
                         r"euse|köchin|modiste|lingère|fleuriste|wirtin|wirthin|ärztin|vorgängerin)\b", re.I)
VORNAMEN_W = {
    "marie", "anna", "rosa", "elise", "emma", "luise", "louise", "bertha", "marg", "sophie", "lina", "ros", "maria",
    "ida", "elisab", "kath", "emilie", "martha", "magd", "julie", "sus", "adele", "verena", "karol", "rosina",
    "magdal", "soph", "lse", "mina", "fanny", "elisabeth", "pauline", "karoline", "klara", "frieda", "céc",
    "josephine", "henr", "johanna", "ver", "barb", "hedw", "elis", "augusta", "mathilde", "math", "clara",
    "lisette", "susanna", "barbara", "helene", "lydia", "therese", "charlotte", "caroline", "henriette", "olga",
    "alice", "hedwig", "agnes", "amalie", "margaritha", "margaretha", "katharina", "rosalie", "albertine", "jenny",
    "laura", "marianne", "marianna", "elisa", "lea", "flora", "wilhelmine", "friederike", "cäcilie", "antoinette",
    "magdalena", "rosine", "emilia", "pauline", "bertha", "berta", "nanette", "mar", "luisa", "lisa", "frida",
}


def frau(r: dict) -> str:
    """witwe, fraeulein, frau (ausdrücklich so bezeichnet), weiblich (nur an Beruf oder Vorname erkannt) oder ''."""
    stand = f"{r['civil_status']} {r['forename']}"
    if WITWE.search(stand) or re.match(r"\s*(?:d\.|des|der)\s", r["occupation_raw"]) and WITWE.search(r["text"]):
        return "witwe"
    if FRAEULEIN.search(stand):
        return "fraeulein"
    if FRAU.search(stand):
        return "frau"
    vorname = re.split(r"[ .]", r["forename"].strip().lower())[0]
    if vorname in VORNAMEN_W or WEIBL_BERUF.match(r["occupation_raw"].split(",")[0].split(" u. ")[0].strip()):
        return "weiblich"
    return ""


# ── Zähler: Sektor aus der Berufsangabe ──────────────────────────────────────────────────────────────
# Einteilung wie in BERNHIST (Volkszählung 1910): 1 = Urproduktion; 2 = Gewerbe und Industrie mit Bau-,
# Nahrungsmittel-, Bekleidungs- und Reinigungsgewerbe (Coiffeur, Wäscherin, Glätterin) und Druck;
# 3 = Handel, Banken, Gastgewerbe, Verkehr, Verwaltung, freie Berufe, persönliche Dienste.
# Es gilt die erste Berufsangabe (bis zum ersten Komma); stehen dort mehrere Wörter, entscheidet das
# früheste, bei gleichem Ort die Reihenfolge 1 – Handel – 3 – 2.
OHNE = re.compile(r"^privati|^privat\.?$|^priv\.?$|^rent|^particul|^partikul|\bstud\b|student|pensionär|\bcand\b|"
                  r"^(?:sohn|vater|tochter|mutter|jun|sen)\b|^gew(?:es)?\b|^alt\b|^alt-|^a\. ", re.I)
KEINE = re.compile(r"^(?:schwestern|schwest|geschw|jgr|jgfr|frl|frau|wwe|wit+we)\.?$", re.I)  # Stand statt Beruf
ANGEHOERIG = re.compile(r"^(?:d\.|des|der) ", re.I)  # «des Schusters Wwe.»
S1 = re.compile(r"landw|handelsgärtn|gärtner(?!in\b)|(?<!kinder)gärtnerin|gärtnerei|^pächter|küher|förster|bannwart|"
                r"lehenmann|gutsbesitz|\bfischer\b|melker|holzhauer|holzspalt|\bbauer\b|karrer\b.*gut|"
                r"landarbeit|rebmann|^oekonom", re.I)
HANDEL = re.compile(
    r"handel|handl|hdl|ändl|haendl|negt|\bneg\b|negot|\bi\. fa\b|\bfirma\b|\bfma\b|drog|confection|konfektion|"
    r"dépot|dépôt|verlag|verleger|lumpensamml|sensal|\bkfm\b|négoc|negoc|kaufm|commis|kommis|krämer|grempl|trödl|hausier|"
    r"agent|reisend|bank|banq|prokur|procur|buchhalt|buchh\b|korrespond|versicher|assekur|makler|comptoir|"
    r"magaz|ladent|ladend|verkäuf|geschäft|gesch\b|spezier|spezer|spezier|mercer|quincaill|bonneter|"
    r"drogu|comestibl|cigarr|zigarr|tabak|waaren\b|waren\b|artikel|lager\b|depot|antiquar|exped|kolonial|"
    r"colonial|associé|\bin fa\b|\bin firma\b|vertret|repräsent|kommission|commission|import|export|"
    r"\ben gros\b|bazar|papeterie|librairie|kiosk|krämerei|\bladen\b|marktfahr", re.I)
S3 = re.compile(
    r"\bpost|bahn|kindergärt|erzieh|vorgänger|halter|brief|concierge|evangelist|pharmac|hausvater|hausmutter|"
    r"copist|kopist|umbiet|geistlich|bischof|theolog|assistent|si[e]?grist|küster|\bbad|lehr\b|brasserie|"
    r"gouvern|institutr|vorst\b|subst\b|telegr|teleph|tram|kondukt|conduct|lokomotiv|locomotiv|zugf|weichen|brems|\bheizer|kutscher|"
    r"droschk|fuhr|camion|\bkarrer|dienstm|diensm|packer|träger|spedit|schiff|manöv|rangier|visiteur|"
    r"beamt|sekret|\bsekr\b|kanzl|revis|adjunkt|\br[aä]th?\b|rath?\b|richter|notar|fürspr|advok|anwalt|weibel|"
    r"polizi|polizei|landjäg|inspekt|inspect|direkt|direct|verwalt|schreiber|kassier|kontrol|control|statist|"
    r"registr|archiv|bibliothek|offiz|oberst|major|hauptm|lieut|leutn|instrukt|instruct|gesandt|attaché|konsul|"
    r"consul|bundes|eidg|kanton|gemeinde|städt|\bstadt|zoll|ohmgeld|kommiss|commiss|präsident|schaffner|"
    r"einnehmer|verweser|vorsteher|aufseher|chef\b|aktuar|substitut|rechnungsf|sachwalt|geometer|ingenieur|"
    r"\bingen\b|techniker|topograph|kartograph|übersetz|planton|korporal|wachtm|soldat|feldweibel|kommand|"
    r"lehrer|lehrerin|professor|\bprof\b|dozent|docent|rektor|pfarrer|\bpfr\b|prediger|mission|vikar|pastor|"
    r"helfer\b|sigrist|\barzt|ärzt|arzt\b|hebamme|apoth|wärter|zahn|pfleg|diakon|masseu|schröpf|"
    r"\bwirt|wirth|wirtschaft|wirtin|hotel|hôtel|pension(?!är)|restaur|kostgeb|café|cafe\b|kaffee|gasthof|"
    r"gasthaus|kellner|\bkoch\b|köchin|portier|pörtner|speise|zimmerverm|logis|"
    r"magd|knecht|diener|bedient|haushält|abwart|abwärt|hauswart|hauswärt|wächter|ausläufer|bureau|büro|"
    r"angestellt|angest\b|gehülf|gehilf|\bgeh\b|"
    r"musik|sänger|pianist|organist|kapellm|journal|redakt|redact|schriftstell|kunstmaler|bildhauer|künstler|"
    r"schauspiel|chemiker|mathemat|gelehrt|korrektor|stenogr|dolmetsch|leichenbitt|totengräb|kaminfeger|"
    r"zuchtmeister|wegmeister|wegknecht|bereiter|pferdew|pferded|stallm|badw|bademeist|nachtwäch", re.I)
S2 = re.compile(
    r"macher|münzarb|bandag|orthop|müller\b|hobler|unternehm|conditor|brod(?:eu|ier)|käser|kässalz|kuttler|"
    r"\bmech\b|stereotyp|kübler|tapez|tischler|silberarb|goldarb|gold- u|schnitzl|graph\b|graphie|"
    r"stein(?:br|me)|parkett|zuschn|zusn|damenschn|destill|gräber|faktor|\bhut(?:arb|rüst|riest|-)|schuhm|schuster|cordonn|schneid|taill|näh|schreiner|ebenist|schlosser|schmied|schmid\b|spengler|"
    r"maler|lackier|gipser|gypser|gyser|maurer|zimmerm|zimmerp|zimmerg|zimmermstr|steinh|dachdeck|hafner|küfer|"
    r"wagner|sattler|tapezier|drechsler|glaser|buchbind|buchdr|setzer|schrifts|drucker|lithogr|typogr|xylogr|"
    r"graveur|stecher|mechanik|mechan\b|monteur|giesser|dreher|bäcker|bäck\b|metzg|\bmüller|brauer|konditor|"
    r"confis|zuckerb|pâtiss|coiff|barbier|wäscher|wascher|wasch|glätter|calandr|lingère|lingere|modist|weber|"
    r"spinner|färber|gerber|seiler|bürsten|korb|flecht|pfläst|cement|parquet|bodenleg|asphalt|elektr|installat|"
    r"uhrenm|uhrm|goldarb|büchsenm|fabrik|geselle|\bges\b|meister|mstr\b|polier|vergold|optiker|strick|stick|"
    r"kürschn|posament|photogr|bauunter|baumeist|architek|architec|\barchit\b|bautechn|bauführ|bauzeichn|"
    r"zeichner|gasarb|gasanz|bauamt|zeughausarb|schleifer|feiler|feilenh|säger|brenner|ziegler|zügler|gürtler|"
    r"kupfer|zinng|blech|kessler|nagler|schäfte|chemis|kleider|schirm|kappen|handarbeiterin|einleger|"
    r"maschin|heizer\b.*fabrik|fumiste|marbrier|bijout|goldschm|instrumentenm|klavierst|orgelb|wagenb|"
    r"vorarbeiter|werkführ|bleich|appret|gilet|corset|korsett|blumenm|fleurist|feger|kunstwasch|"
    r"buchdruckerei|bäckerei|metzgerei|schlosserei|schreinerei|giesserei|brauerei|gerberei|färberei|weberei|"
    r"spinnerei|ziegelei|mühle\b|werkstätte|atelier|manufact|manufakt", re.I)
UNBESTIMMT = re.compile(r"taglöhn|tagl\b|handlang|arbeiter|arb\b|lehrling|lehrtochter|gehülfe|aushülf", re.I)


def erste_angabe(beruf: str) -> str:
    """Die Berufsangabe bis zum ersten Komma; «Milch-, Anken- u. Käsehändler» bleibt ganz."""
    teile, out = re.split(r"[,(;]", beruf.strip()), []
    for t in teile:
        out.append(t.strip())
        if not t.strip().endswith("-"):
            break
    return " ".join(out).strip()


def sektor(beruf: str, titel: str = "", witwe: bool = False) -> str:
    """'1', '2', '3', 'ohne' (kein Erwerb genannt: Privatier, «gew.», «des Schusters Wwe.»), 'unbestimmt'
    (Beruf genannt, aber keinem Sektor zuzuweisen) oder '' (keine Angabe)."""
    kopf = erste_angabe(beruf).lower()
    kopf = re.sub(r"(\w)-\s+(?=[a-zäöü])(?!u\.|und\b)", r"\1", kopf)  # «Wirt-schaft» am Zeilenende
    if not kopf:
        t = titel.lower()
        return "3" if re.search(r"dr\b|prof|pfr|r[aä]th?\b|oberst|major|hauptm|direkt|richter|ingen", t) else ""
    if KEINE.match(kopf):
        return ""
    if ANGEHOERIG.match(kopf):
        if witwe:
            return "ohne"
        kopf = ANGEHOERIG.sub("", kopf)
    if OHNE.search(kopf):
        return "ohne"
    treffer = [(m.start(), rang, s) for rang, (rx, s) in
               enumerate(((S1, "1"), (HANDEL, "3"), (S3, "3"), (S2, "2"))) if (m := rx.search(kopf))]
    if treffer:
        return min(treffer)[2]
    return "unbestimmt"


def sektor_von(r: dict) -> str:
    return sektor(r["occupation_raw"], r["title"], frau(r) == "witwe")


# ── Zähler: einzelne Gruppen ─────────────────────────────────────────────────────────────────────────
GRUPPEN = {
    "aerzte": re.compile(r"arzt\b|ärztin|aerztin", re.I),
    "lehrpersonen_alle": re.compile(r"lehrer(?:in|innen)?\b", re.I),
    "spezerei": re.compile(r"spez[ei]r|kolonial|colonial|épicer", re.I),
    "dienstboten": re.compile(r"^(?:haus|stall|privat|dienst|stuben|kinds|kammer|offiziers ?-? ?)?(?:magd|knecht|köchin|"
                              r"diener|bedienter|jungfer|frau|mädchen)|^haushälterin|^dienstbot|^domesti|^bonne\b", re.I),
    "tagloehner": re.compile(r"taglöhn|tagl\b|handlang", re.I),
}
NICHT_ARZT = re.compile(r"zahn|tier|thier|vieh|pferde", re.I)
# Lehrpersonen an öffentlichen Volksschulen: die Zahl von 1895 (131 bei 5151 Schülern) meint die Primarschule.
PRIMAR = re.compile(r"primar|oberlehrer|längg|matten|lorraine|friedbühl|sulgenbach|breitenrain|postgass|"
                    r"kirchenfeld|schosshalde|brunnmatt|unter(?:n|en) stadt|mittl|ob(?:ern|eren|\.) stadt|spitalacker", re.I)
NICHT_VOLKSSCHULE = re.compile(r"alt|gewes|lerber|mädchensch|israel|isr\.|buchhalt|mathem|beschlag|stick|piano|klav|"
                               r"clav|institut|waisen|pension|musik|klavier|gesang|sprach|tanz|turn|fecht|reit|zeichn|arbeits|gymnas|sekund|"
                               r"sek\.|progymn|seminar|kunst|privat|haus|handels|gewerb|kleinkinder|kinderg|"
                               r"violin|zither|schwimm|französ|engl|ital|taubst|blinden|\bgew\b", re.I)


def gruppe(name: str, beruf: str, titel: str = "") -> bool:
    kopf = erste_angabe(beruf)
    if name == "aerzte":
        return bool(GRUPPEN[name].search(kopf) and not NICHT_ARZT.search(kopf))
    if name == "aerzte_med":  # dazu alle mit Titel «Dr. med.», auch wenn der Beruf anders lautet
        return gruppe("aerzte", beruf) or bool(re.search(r"\bmed\b", titel, re.I) and not re.search(
            r"cand|vet|dent", titel, re.I) and not NICHT_ARZT.search(beruf))
    if name == "lehrpersonen_primar":
        return bool(GRUPPEN["lehrpersonen_alle"].search(kopf) and PRIMAR.search(kopf) and not re.search(r"\bgew|\balt", kopf, re.I))
    if name == "lehrpersonen_volksschule":
        return gruppe("lehrpersonen_primar", beruf) or bool(GRUPPEN["lehrpersonen_alle"].search(kopf) and not NICHT_VOLKSSCHULE.search(kopf))
    return bool(GRUPPEN[name].search(kopf))


RUBRIK = {  # Rubriken des Berufsregisters
    "aerzte": re.compile(r"^(?:\w\) ?)?(?:aerzte|ärzte)\b", re.I),
    "spezerei": re.compile(r"spez[ei]re", re.I),
    "lehrpersonen_alle": re.compile(r"lehrer", re.I),
    "hebammen": re.compile(r"hebamm", re.I),
}


# ── Zählen ───────────────────────────────────────────────────────────────────────────────────────────
def norm(s: str) -> str:
    return re.sub(r"[^a-zäöüéèàç]", "", s.lower().replace("ae", "ä").replace("oe", "ö").replace("ue", "ü"))


def person_key(r: dict) -> tuple:
    return (norm(r["surname"]), norm(r["forename"]), norm(r["alliance_name"]))


def lade(name: str) -> list[dict]:
    return lies(CSV_DIR / name)


def zaehle(einwohner: list[dict], berufe: list[dict], band: str) -> dict:
    """Alle Zähler eines Bands."""
    e = [r for r in einwohner if r["volume"] == band]
    b = [r for r in berufe if r["volume"] == band]
    z: dict = {"eintraege": len(e), "art": Counter(art(r) for r in e)}
    p = [r for r in e if art(r) == "person"]
    z["personen"] = len(p)
    z["namen_verschieden"] = len({person_key(r) for r in p})
    z["frau"] = Counter(frau(r) for r in p)
    z["frauen"] = sum(n for k, n in z["frau"].items() if k)
    sek = Counter(sektor_von(r) for r in p)
    z["sektor"] = sek
    z["erwerb"] = sek["1"] + sek["2"] + sek["3"] + sek["unbestimmt"]
    z["erwerb_frauen"] = sum(1 for r in p if frau(r) and sektor_von(r) in ("1", "2", "3", "unbestimmt"))
    z["gruppe"] = {g: sum(1 for r in p if gruppe(g, r["occupation_raw"], r["title"]))
                   for g in ("aerzte", "aerzte_med", "lehrpersonen_alle", "lehrpersonen_volksschule", "lehrpersonen_primar",
                             "spezerei", "dienstboten", "tagloehner")}
    z["spezerei_alle"] = sum(1 for r in e if art(r) != "verweis" and gruppe("spezerei", r["occupation_raw"]))
    # Berufsregister
    z["register"] = len(b)
    z["register_art"] = Counter(art(r) for r in b)
    bp = [r for r in b if art(r) != "verweis"]
    z["register_einheiten"] = len({(norm(r["surname"]), norm(r["forename"]), norm(r["street_raw"]), r["building_no"]) for r in bp})
    haus = {(norm(r["surname"]), norm(r["street_raw"]), r["building_no"]) for r in e}
    name = {(norm(r["surname"]), norm(r["forename"])[:1]) for r in e}
    z["register_im_einwohner_adresse"] = sum(1 for r in bp if (norm(r["surname"]), norm(r["street_raw"]), r["building_no"]) in haus)
    z["register_im_einwohner_name"] = sum(1 for r in bp if (norm(r["surname"]), norm(r["street_raw"]), r["building_no"]) in haus
                                          or (norm(r["surname"]), norm(r["forename"])[:1]) in name)
    z["register_gezaehlt"] = len(bp)
    z["rubrik"] = {g: sum(1 for r in bp if rx.search(r["heading"])) for g, rx in RUBRIK.items()}
    return z


def zeilen(w: dict[str, float], z: dict[str, dict]) -> list[dict]:
    """Ergebnistabelle: je Band und Gruppe Zähler, Nenner und Quote."""
    out = []
    for band in ("1883", "1900"):
        n, c = nenner(w, band), z[band]
        n["register"] = (c["register_gezaehlt"], "direkt", "Einträge im Berufsregister ohne Verweise")

        def add(gruppe_: str, zaehler, was: str, nen: str | None, bem: str = "") -> None:
            if zaehler is None:  # die Gruppe gibt es in diesem Band nicht
                zaehler, nen = "", None
            wert, art_, her = n[nen] if nen else ("", "", "")
            out.append({"band": BAND[band], "jahr": JAHR[band], "gruppe": gruppe_, "zaehler": zaehler,
                        "zaehler_was": was, "nenner": round(wert) if nen else "", "nenner_art": art_,
                        "nenner_herleitung": her, "quote_prozent": quote(zaehler, wert) if nen else "",
                        "bemerkung": bem})

        add("Einträge im Einwohnerverzeichnis", c["eintraege"], "alle Zeilen", "bevoelkerung", "mit Firmen, Ämtern und Verweisen")
        add("Personen je Einwohner", c["personen"], "Einträge von Personen", "bevoelkerung", "Untergrenze: genannt sind Erwachsene mit eigener Adresse, nicht Köpfe")
        add("Personen je Haushalt", c["personen"], "Einträge von Personen", "haushalte", "über 100 heisst: mehr als eine genannte Person je Haushalt")
        add("Firmen", c["art"]["firma"], "Personenfirmen (&, Cie., Gebr., Söhne, Erben)", None)
        add("Ämter, Vereine, Betriebe", c["art"]["institution"], "Einträge ohne Personenname", None)
        add("Verweise", c["art"]["verweis"], "«s. auch …» ohne Adresse", None, "kein Eintrag im eigentlichen Sinn")
        add("Verschiedene Namen", c["namen_verschieden"], "Name, Vorname und Allianzname verschieden", "bevoelkerung", "Untergrenze der Personenzahl: «Müller, Joh.» steht für mehrere Personen")
        add("Frauen", c["frauen"], "Witwe, Fräulein, Frau oder weiblicher Vorname oder Beruf", "frauen", "Untergrenze: viele Vornamen sind abgekürzt")
        add("Witwen", c["frau"]["witwe"], "«Wwe.», «Wittwe», «Witwe»", "witwen")
        add("Fräulein", c["frau"]["fraeulein"], "«Frl.», «Jgfr.», «Schwestern»", None, "kein Nenner: ledige Frauen sind in BERNHIST nur 1846 ausgewiesen")
        add("Personen mit Erwerb", c["erwerb"], "Berufsangabe in Sektor 1–3 oder unbestimmt", "erwerbstaetige")
        add("Frauen mit Erwerb", c["erwerb_frauen"], "erkannte Frauen mit Berufsangabe", "erwerbstaetige_frauen", "Untergrenze")
        for s, lab in (("1", "1. Sektor"), ("2", "2. Sektor"), ("3", "3. Sektor")):
            add(lab, c["sektor"][s], "Personen nach erster Berufsangabe", f"sektor{s}", "Nenner mit der Struktur von 1910")
        add("Berufsregister: Einheiten", c["register_einheiten"], "verschiedene Namen mit Adresse im Berufsregister", "selbstaendige", "eine Einheit kann in mehreren Rubriken stehen")
        add("Berufsregister: im Einwohnerverzeichnis wiedergefunden", c["register_im_einwohner_name"], "gleicher Name mit gleicher Adresse oder gleichem ersten Buchstaben des Vornamens", "register", "grosszügig: häufige Namen treffen auch Fremde")
        add("Berufsregister: mit gleicher Adresse wiedergefunden", c["register_im_einwohner_adresse"], "gleicher Name, gleiche Strasse und Hausnummer", "register", "streng: Geschäfts- und Wohnadresse weichen oft ab")
        add("Ärzte (Beruf nennt «Arzt»)", c["gruppe"]["aerzte"], "erste Berufsangabe mit «Arzt», ohne Zahn- und Tierärzte", "aerzte_linear")
        add("Ärzte (dazu Titel «Dr. med.»)", c["gruppe"]["aerzte_med"], "wie oben, dazu alle mit «med.» im Titel", "aerzte_linear", "mit Professoren, Beamten und Assistenten")
        add("Ärzte (dazu Titel «Dr. med.», gegen Ärztedichte)", c["gruppe"]["aerzte_med"], "wie oben", "aerzte_dichte")
        add("Ärzte (Rubrik im Berufsregister)", c["rubrik"]["aerzte"] or None, "Rubrik «Aerzte»", "aerzte_linear", "1883–84 hat das Berufsregister keine Rubrik «Aerzte»")
        add("Lehrer und Lehrerinnen (Primarschule genannt)", c["gruppe"]["lehrpersonen_primar"], "«Primarlehrer», «Oberlehrer» oder eine Primarschule der Stadt genannt", "lehrpersonen", "Untergrenze")
        add("Lehrer und Lehrerinnen (ohne Fach- und höhere Schulen)", c["gruppe"]["lehrpersonen_volksschule"], "dazu «Lehrer(in)» ohne nähere Angabe", "lehrpersonen", "enthält Privatschulen; Nenner meint nur die Primarschule")
        add("Lehrer und Lehrerinnen (alle)", c["gruppe"]["lehrpersonen_alle"], "jede Angabe mit «Lehrer(in)»", None, "kein passender Nenner")
        add("Spezereihandlungen (Rubrik im Berufsregister)", c["rubrik"]["spezerei"], "Rubriken mit «Spezerei»", "spezerei")
        add("Spezereihandlungen (Einwohnerverzeichnis)", c["spezerei_alle"], "Angabe mit «Spezerei», «Spezierer», «Kolonial»", "spezerei")
        add("Dienstboten", c["gruppe"]["dienstboten"], "Magd, Knecht, Köchin, Diener, Haushälterin", "dienstboten")
        add("Taglöhner und Handlanger", c["gruppe"]["tagloehner"], "«Taglöhner», «Handlanger»", "tagloehner")
    return out


def wachstum(w: dict[str, float], z: dict[str, dict]) -> list[dict]:
    """Vergleich der Bände: Wachstum des Buchs gegen das der Stadt, 1883 bis 1900."""
    j = JAHR["1900"] - JAHR["1883"]
    n0, n1 = nenner(w, "1883"), nenner(w, "1900")
    paare = [("Wohnbevölkerung (BERNHIST)", n0["bevoelkerung"][0], n1["bevoelkerung"][0]),
             ("Einträge im Einwohnerverzeichnis", z["1883"]["eintraege"], z["1900"]["eintraege"]),
             ("Personen im Einwohnerverzeichnis", z["1883"]["personen"], z["1900"]["personen"]),
             ("erkannte Frauen", z["1883"]["frauen"], z["1900"]["frauen"]),
             ("Firmen", z["1883"]["art"]["firma"], z["1900"]["art"]["firma"]),
             ("Einträge im Berufsregister", z["1883"]["register"], z["1900"]["register"]),
             ("Einheiten im Berufsregister", z["1883"]["register_einheiten"], z["1900"]["register_einheiten"])]
    return [{"groesse": k, "wert_1883": round(a), "wert_1900": round(b), "faktor": round(b / a, 2),
             "prozent_pro_jahr": jahresrate(a, b, j)} for k, a, b in paare]


# ── Stichprobe zur Sektorzuordnung ───────────────────────────────────────────────────────────────────
def stichprobe_ziehen(einwohner: list[dict], n: int, seed: int = 20261121) -> list[dict]:
    """n Personen je Band mit Berufsangabe, fest gesät. Die Spalte `soll` wird von Hand gefüllt."""
    rnd, out = random.Random(seed), []
    for band in ("1883", "1900"):
        pool = [r for r in einwohner if r["volume"] == band and art(r) == "person" and r["occupation_raw"].strip()]
        for r in sorted(rnd.sample(pool, n), key=lambda r: r["entry_id"]):
            out.append({"entry_id": r["entry_id"], "occupation_raw": r["occupation_raw"], "text": r["text"],
                        "title": r["title"], "witwe": "1" if frau(r) == "witwe" else "", "zuordnung": sektor_von(r), "soll": "",
                        "bemerkung": ""})
    return out


def trefferquote(pfad: Path = STICHPROBE) -> tuple[int, int, int]:
    """(geprüft, richtig, davon mit heute anderer Zuordnung als bei der Prüfung)."""
    rows = [r for r in lies(pfad) if r["soll"]]
    jetzt = [sektor(r["occupation_raw"], r["title"], r["witwe"] == "1") for r in rows]
    richtig = sum(1 for r, s in zip(rows, jetzt) if s == r["soll"])
    geaendert = sum(1 for r, s in zip(rows, jetzt) if s != r["zuordnung"])
    return len(rows), richtig, geaendert


# ── Ausgabe ──────────────────────────────────────────────────────────────────────────────────────────
def schreibe(pfad: Path, felder: list[str], rows: list[dict]) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=felder, lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)


def zahl(x) -> str:
    if x == "":
        return "–"
    if isinstance(x, float) and x != round(x):
        return f"{x:.1f}".replace(".", ",")
    if isinstance(x, str):
        return x
    return f"{round(x):,}".replace(",", " ")


def tabellen(rows: list[dict], wach: list[dict], sek: list[dict], tq: tuple[int, int, int]) -> str:
    t = ["| Gruppe | 1883–84: Buch | Nenner | Quote | 1900: Buch | Nenner | Quote |", "|---|---:|---:|---:|---:|---:|---:|"]
    by = {(r["band"], r["gruppe"]): r for r in rows}
    for g in dict.fromkeys(r["gruppe"] for r in rows):
        a, b = by[("1883–84", g)], by[("1900", g)]
        q = lambda r: "–" if r["quote_prozent"] == "" else f"{float(r['quote_prozent']):.1f} %".replace(".", ",")
        t.append(f"| {g} | {zahl(a['zaehler'])} | {zahl(a['nenner'])} | {q(a)} | {zahl(b['zaehler'])} | {zahl(b['nenner'])} | {q(b)} |")
    t += ["", "Verteilung der Personen nach erster Berufsangabe (Anteile in Prozent der Personen mit Sektor):", "",
          "| | 1883–84: Personen | Anteil | 1900: Personen | Anteil | BERNHIST 1856 | BERNHIST 1910 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in sek:
        t.append(f"| {r['zeile']} | {zahl(r['n_1883'])} | {r['anteil_1883']} | {zahl(r['n_1900'])} | {r['anteil_1900']} | {r['bernhist_1856']} | {r['bernhist_1910']} |")
    t += ["", f"Stichprobe zur Sektorzuordnung: {tq[1]} von {tq[0]} Berufsangaben richtig zugeordnet "
              f"({zahl(100 * tq[1] / tq[0]) if tq[0] else '–'} %).", "",
          "Wachstum 1883 bis 1900:", "", "| Grösse | 1883 | 1900 | Faktor | pro Jahr |", "|---|---:|---:|---:|---:|"]
    for r in wach:
        t.append(f"| {r['groesse']} | {zahl(r['wert_1883'])} | {zahl(r['wert_1900'])} | {str(r['faktor']).replace('.', ',')} | {str(r['prozent_pro_jahr']).replace('.', ',')} % |")
    return "\n".join(t)


def sektor_tabelle(w: dict[str, float], z: dict[str, dict]) -> list[dict]:
    out = []
    pct = lambda a, b: f"{100 * a / b:.1f}".replace(".", ",") if b else "–"
    tot = {b: sum(z[b]["sektor"][s] for s in "123") for b in z}
    for s in "123":
        out.append({"zeile": f"{s}. Sektor", "n_1883": z["1883"]["sektor"][s], "anteil_1883": pct(z["1883"]["sektor"][s], tot["1883"]),
                    "n_1900": z["1900"]["sektor"][s], "anteil_1900": pct(z["1900"]["sektor"][s], tot["1900"]),
                    "bernhist_1856": pct(w[f"erw_s{s}_1856"], w["erw_1856"]), "bernhist_1910": pct(w[f"erw_s{s}_1910"], w["erw_1910"])})
    for k, lab in (("unbestimmt", "Beruf ohne Sektor (Taglöhner, Arbeiter …)"), ("ohne", "ohne Erwerb (Privatier, «gew.», Witwe des …)"), ("", "keine Angabe")):
        out.append({"zeile": lab, "n_1883": z["1883"]["sektor"][k], "anteil_1883": "", "n_1900": z["1900"]["sektor"][k],
                    "anteil_1900": "", "bernhist_1856": "", "bernhist_1910": ""})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bernhist", type=Path, default=os.environ.get("BERNHIST_SQLITE"),
                    help="lokale SQLite-Datei des BERNHIST-Dumps; ohne sie gelten die Werte in ref/bernhist/werte.csv")
    ap.add_argument("--stichprobe", type=int, metavar="N", help="Stichprobe mit N Einträgen je Band neu ziehen (überschreibt die Urteile)")
    args = ap.parse_args()
    if args.bernhist:
        schreibe(WERTE, WERTE_FELDER, werte_aus_dump(Path(args.bernhist)))
        print(f"BERNHIST-Werte aus {args.bernhist} → {WERTE.relative_to(ROOT)}")
    w = werte_laden()
    einwohner, berufe = lade("04_entries.csv"), lade("04_berufe.csv")
    if args.stichprobe:
        s = stichprobe_ziehen(einwohner, args.stichprobe)
        schreibe(STICHPROBE, list(s[0]), s)
        print(f"Stichprobe: {len(s)} Einträge → {STICHPROBE.relative_to(ROOT)} (Spalte «soll» von Hand füllen)")
    z = {b: zaehle(einwohner, berufe, b) for b in ("1883", "1900")}
    rows, wach, sek = zeilen(w, z), wachstum(w, z), sektor_tabelle(w, z)
    schreibe(OUT_DIR / "abdeckung.csv", list(rows[0]), rows)
    schreibe(OUT_DIR / "wachstum.csv", list(wach[0]), wach)
    schreibe(OUT_DIR / "sektoren.csv", list(sek[0]), sek)
    tq = trefferquote() if STICHPROBE.exists() else (0, 0, 0)
    block = tabellen(rows, wach, sek, tq)
    if DOC.exists():
        text = DOC.read_text(encoding="utf-8")
        neu = re.sub(r"(<!-- TABELLEN:START -->\n).*?(<!-- TABELLEN:ENDE -->)", lambda m: m.group(1) + block + "\n" + m.group(2), text, flags=re.S)
        DOC.write_text(neu, encoding="utf-8")
    print(block)
    for b in z:
        print(b, {k: (dict(v) if isinstance(v, Counter) else v) for k, v in z[b].items()})


if __name__ == "__main__":
    main()
