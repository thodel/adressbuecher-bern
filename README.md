# Adressbücher der Stadt Bern 1861–1900

Einträge der Berner Adressbücher, maschinell gelesen. Quelle für
[Vernetzte Schweiz 1860–1914](https://thodel.github.io/vernetzte-schweiz/), wo sie mit den
Telefonbüchern und den anderen Adressbüchern verknüpft werden. Die frühen Berner Adressbücher
(1795–1839) liegen in [adressbuecher-bern-frueh](https://thodel.github.io/adressbuecher-bern-frueh/).

Seit November 2026 kommen die Bände 1861–1914 von e-rara dazu (`scripts/weekly/`): die Fraktur-Bände
1861–1879 gelesen mit Gemini, die Antiqua-Bände 1881–1914 mit qwen3.8. Bei 1883–84 und 1900 nennt «Seiten»
die Seite im PDF, bei den übrigen Bänden die Bildnummer bei e-rara.

| Band | Seiten | Einwohner | Berufsregister | Leser | Stichprobe |
|---|---:|---:|---:|---|---:|
| Adressbuch der Stadt Bern 1861 | 236 | 4 073 (Bild 79–145) | 2 361 (Bild 146–184) | Gemini | 16/20 |
| Adressbuch der Stadt Bern 1862 | 260 | 4 096 (Bild 87–157) | 2 604 (Bild 158–200) | Gemini | 16/20 |
| Adressbuch der Stadt Bern 1863 | 260 | 4 053 (Bild 85–156) | 2 685 (Bild 157–200) | Gemini | 18/20 |
| Adressbuch der Stadt Bern 1865 | 284 | 4 240 (Bild 94–169) | 2 831 (Bild 170–218) | Gemini | 17/20 |
| Adressbuch der Stadt Bern 1866 | 307 | 4 882 (Bild 101–186) | 3 160 (Bild 187–238) | Gemini | 17/20 |
| Adressbuch der Stadt Bern 1867–68 | 344 | 5 090 (Bild 106–200) | 3 292 (Bild 201–255) | Gemini | 66/80 |
| Adressbuch der Stadt Bern 1868 | 360 | 5 354 (Bild 113–214) | 3 429 (Bild 215–274) | Gemini | 18/20 |
| Adressbuch der Stadt Bern 1870 | 363 | 6 087 (Bild 117–236) | 3 420 (Bild 237–296) | Gemini | 18/20 |
| Adressbuch der Stadt Bern 1871 | 391 | 5 996 (Bild 123–242) | 3 373 (Bild 243–301) | Gemini | 16/20 |
| Adressbuch der Stadt Bern 1873 | 412 | 5 710 (Bild 131–249) | 3 265 (Bild 250–308) | Gemini | 17/20 |
| Adressbuch der Stadt Bern 1875 | 448 | 6 122 (Bild 145–278) | 3 483 (Bild 279–342) | Gemini | 18/20 |
| Adressbuch der Stadt Bern 1877 | 494 | 6 445 (Bild 138–283) | 3 727 (Bild 284–354) | Gemini | 19/20 |
| Adressbuch der Stadt Bern 1879 | 514 | 6 232 (Bild 138–277) | 3 898 (Bild 278–355) | Gemini | 18/20 |
| Adressbuch der Stadt Bern 1883–84 | 335 | 8 241 (S. 83–192) | 4 226 (S. 193–246) | qwen3.8 | 61/73 |
| Adressbuch der Stadt Bern 1900 | 677 | 15 182 (S. 142–385) | 7 094 (S. 386–491) | qwen3.8 | 121/146 |

## Seite

Durchsuchbare Seite mit allen Einträgen, Filtern nach Band, Strasse, Konfidenz und Hinweis, Link je Zeile
auf die Seite bei e-rara und Flagging je Zeile (wie bei Aarau, Basel und Baden):
https://thodel.github.io/adressbuecher-bern/

- `python scripts/90_seite.py --out _site` baut sie lokal (`index.html` und je Band `data/<Band>.json`,
  die die Seite erst bei Bedarf lädt); GitHub Actions (`.github/workflows/pages.yml`) baut und
  veröffentlicht sie bei jedem Push, der Daten oder Skript ändert.
- `web/erara_pages.csv`: PDF-Seite → e-rara-Canvas (1883–84 titleinfo 1396077, 1900 titleinfo 1704646;
  PDF-Seite k = Canvas k−1, weil das PDF ein Deckblatt hat).
- Karte: `python scripts/92_karte.py --out _site/karte.html` (Kreise je Strasse).
- Verknüpfungen in `web/`, mit den Skripten erzeugt und eingecheckt, damit der Bau ohne Netz und ohne
  vernetzte-schweiz läuft:
  - `telefon.csv` (`scripts/80_telefon.py --vs …`): Einträge mit ☎ → PTT-Telefonbuch (gedruckte Nummer + Name,
    sonst Verknüpfung von Vernetzte Schweiz), mit Link auf die Person und das Seitenbild; Commit in `telefon_source.txt`.
  - `baende.csv` (`scripts/81_baende.py`): dieselbe Person im anderen Band.
  - `normdaten.csv` (`scripts/82_normdaten.py --vs …`): ungeprüfte Kandidaten aus HLS und Wikidata.
  - `geo/` (`scripts/10_geo.py`): Strassen nach der Hausnummerierung 1882 (aus adressbuecher-bern-frueh) und OpenStreetMap (Nominatim, Cache in `geo/nominatim_cache.json`).
  - Je Zeile ausserdem ein Link auf die Siegfriedkarte des Jahres (swisstopo Zeitreise).
- Abdeckung: `python scripts/93_abdeckung.py --out _site/abdeckung.html` (Unterseite aus `data/abdeckung/`).
- Flags von der Seite: CSV exportieren, `python scripts/91_merge_flags.py <datei.csv>`, committen.
- Plan für weitere Teile (Karte über die Hausnummern 1882, Häuserverzeichnis): `docs/SITE_PLAN.md`.

## Abdeckung, gemessen an BERNHIST

Wie viel von der Stadt steht im Buch? `docs/abdeckung.md` misst die beiden Bände an den Zahlen von
[BERNHIST](https://www.bernhist.ch) für die Stadt Bern; auf der Seite steht das Ergebnis unter
[Abdeckung](https://thodel.github.io/adressbuecher-bern/abdeckung.html).

| | 1883–84 | 1900 |
|---|---:|---:|
| Personen im Einwohnerverzeichnis | 7 969 | 14 184 |
| je 100 Einwohner | 18,0 | 22,1 |
| je 100 Haushalte (Haushalte geschätzt) | 83 | 102 |
| erkannte Frauen, Anteil an den Frauen der Stadt | 6,6 % | 9,0 % |
| Dienstboten im Buch | 16 | 24 |

- `python scripts/85_abdeckung.py` rechnet alles neu (`data/abdeckung/*.csv`, Tabellen in `docs/abdeckung.md`).
  Mit `--bernhist <sqlite>` oder `BERNHIST_SQLITE` liest es die Nenner neu aus dem lokal geladenen Dump,
  sonst aus `ref/bernhist/werte.csv`.
- `ref/bernhist/werte.csv`: die 44 verwendeten Einzelwerte mit Ort, Thema, Jahr und Quelle. Der Dump liegt
  nicht hier. BERNHIST steht unter der MIT-Lizenz (© 2019 Universität Bern, Universitätsbibliothek); `ref/bernhist/`
  übernimmt sie (`ref/bernhist/LICENSE`) und fällt nicht unter die CC0-Freigabe.
- `data/abdeckung/stichprobe_sektor.csv`: 80 Berufsangaben mit Urteil zur Sektorzuordnung (78 richtig).
- Die Spalte `entry_type` trennt Personen und Firmen nicht zuverlässig (sie trifft auch «Gesellschaftsstrasse»);
  die Messung bestimmt die Art neu, die CSV bleibt, wie sie ist.

## Dateien

Schema wie [adressbuecher-aarau](https://github.com/thodel/adressbuecher-aarau), dazu `municipality`
(hier immer «Bern») und `qa_flags`.

- `data/csv/04_entries_<Band>.csv`: Einwohnerverzeichnisse, eine Datei je Band.
- `data/csv/04_berufe_<Band>.csv`: Berufsregister (1900 mit den patentierten Berufen, Gasthöfen und
  Wirtschaften); der Beruf steht in `heading`. Bis 26.11.2026 standen alle Bände in je einer Datei
  `04_entries.csv` und `04_berufe.csv`; mit den Bänden 1861–1914 würden sie zu gross für GitHub.
- `data/csv/00_volumes.csv`: die Bände; Seite, Karte und Skripte nehmen die Bandliste von hier
  (`scripts/baende.py`). Kennungen sind Zeichenketten (Supplemente `1893s`, `1896s`).
- `data/csv/03_sections.csv`: Seitenbereiche je Band.
- `data/csv/10_authority_links.csv`: leer; Normdaten verknüpft «Vernetzte Schweiz» über die Personen.
- `data/qwen/<Band>/`, `data/gemini/<Band>/`: die Lesung, wie sie vom Modell kam (qwen3.8 bzw. Gemini).
- `data/review/weekly_<Band>.csv`: Stichprobe der Bände ab 1861 (20 Einträge, am Seitenbild geprüft).

`python scripts/convert.py` erzeugt `data/csv/` aus `data/qwen/` und `data/gemini/`; `python -m unittest discover -s tests`.

## Wie gelesen

- **Modell (1883–84, 1900, Antiqua-Bände 1881–1914):** `qwen3.8-27b` auf GPUStack der Universität Bern,
  Seitenbild 2× vergrössert, Ausgabe als JSON-Zeilen. Vorlage sind die PDFs von e-rara (700–1000 px breite
  Bilder), ab 1881 die Seitenbilder über IIIF.
- **Modell (Fraktur-Bände 1861–1879):** `gemini-3.5-flash` von Google (die Antwort nennt `gemini-3.6-flash`),
  Seitenbilder über IIIF bis 1600 px breit (`scripts/weekly/be_gemini.py`); `parse_method` nennt den Leser
  je Eintrag. Kosten 1861 4,88 $ (106 Seiten), 1862 5,37 $ (116 Seiten), 1863 5,28 $ (116 Seiten), 1865 5,73 $
  (127 Seiten), 1866 6,37 $ (140), 1867 6,64 $ (150), 1868 7,07 $ (164), 1870 7,71 $ (182), 1871 7,67 $ (181), 1873 7,28 $ (179),
  1875 7,88 $ (200), 1877 8,41 $ (218), 1879 8,57 $ (219).
- **Fraktur-Bände, was convert.py ergänzt:** Im Berufsregister setzt ein Eintrag oben auf einer Seite ohne
  Rubrik die letzte Rubrik der Vorseite fort (`qa_flags` «rubrik_vorseite»); einen Absatz im Fliesstext
  (1861, Bild 166–184) teilt es in Einträge («fliesstext»); «=» vor einem Namen ist ein Allianzname zum
  vorigen Familiennamen. Auf einigen Seiten gab das Modell nur die Felder, nicht die gelesene Zeile
  («ohne_text»; 1861 2 Seiten, 1862 4, 1863 3, 1865 1, 1866 2, 1867 3, 1868 2, 1870 4, 1873 6, 1875 5, 1877 5,
  1879 2). Ab 1873 beginnt der Abschnitt «X. Wirthschaften» auf der letzten Seite des Berufsregisters;
  convert.py schneidet dort ab (`cut_wirthschaften`). Auf vier Seiten liess das Modell `"type": "entry"` weg,
  und collect.py auf tei übernahm sie nicht (1866 Bild 208, 1867 Bild 219 und 228, 1879 Bild 354); für diese
  Bände ist `entries.csv` mit einer Kopie von collect.py gesammelt, die auch solche Zeilen nimmt.
- **Stichprobe, von Hand am Seitenbild:** 1883–84 61 von 73 Einträgen voll korrekt (84 %), 1900 121 von
  146 (83 %). Die Fehler sind meist einzelne Buchstaben in Namen und Strassen. 1861 und 1862 je 16 von 20
  (80 %, `data/review/weekly_<Band>.csv`): Buchstaben in Strassenkürzeln («Mtzg.» für «Metzg.»), einmal F
  als J gelesen, eine Firma nur mit dem ersten Namen, eine zweite Hausnummer weggelassen. 1863 18 von 20
  (90 %): ein «=» vor dem Allianznamen übersehen, ein Ort im Beruf («Gutsbes. in Dießbach») nur im Text.
  1865 17 von 20 (85 %): eine Rubrik verlesen («Brodieriewaarenhändler»), «Mezg.» für «Metzg.», eine Firma
  nur mit dem ersten Namen. 1866 17 von 20, 1868 18, 1870 18, 1871 16, 1873 17, 1875 18, 1877 19, 1879 18
  (zusammen 141 von 160, 88 %): meist Strassenkürzel («Mezgg.» für «Metzg.»), ein Ort im Beruf, F/J und
  einzelne Buchstaben in Namen («Rikli» für «Rickli»), «v.» im Stand statt im Familiennamen, eine Rubrik leer.
  1867 zuerst 14 von 20, mit 60 weiteren Einträgen (zweite Ziehung, Seed 186760) 66 von 80 (83 %): meist
  Strassenkürzel (die tz-Ligatur als z: «Mezg.», «Mzg.»), zweimal ein Name aus der Vorzeile falsch geerbt,
  eine erste von zwei Adressen fehlt. Zurückgestellt (Stichprobe unter 80 %): 1864, 63 von 80 (79 %;
  tz-Ligatur, Namen verlesen wie «Zobrist» für «Joß»; dazu fehlt Bild 213, die letzte Seite des
  Berufsregisters). Im Berufsregister 1862 waren bis 26.11.2026 die Wirthschaften (Bild 201–202, 68
  Einträge) mitgezählt.
- Keine Nachkorrektur; `qa_flags` markiert Verdachtsfälle.

## Nicht übernommen

Behörden, Vereine, Häuser- und Eigentümerverzeichnisse (1883–84 S. 247–277, 1900 S. 492–544), Stadtplan,
Tarife, Inserate. Das Heft «Die Häuser-Nummerirung in Bern» (1882) ist gelesen, aber noch nicht hier.
Der Band 1860 (Fraktur) ist nicht ganz gelesen: in der Probe waren nur 40–60 % der Einträge korrekt.

## Lizenz

Die Bücher sind vor 1914 erschienen; ihr Inhalt ist gemeinfrei (URG Art. 2 Abs. 1, Art. 29 Abs. 2).
Die Daten in `data/` stehen unter [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), der Code
unter MIT. Gelesen haben qwen3.8 (1883–84, 1900) und Gemini (1861–1863, 1865–1868, 1870, 1871, 1873, 1875, 1877, 1879); der Leser steht je Eintrag in
`parse_method`. Die Scans liegen nicht in diesem Repo. `ref/bernhist/` enthält Einzelwerte aus BERNHIST und
steht wie BERNHIST unter der MIT-Lizenz (© 2019 Universität Bern, Universitätsbibliothek; `ref/bernhist/LICENSE`).
