# Adressbücher der Stadt Bern 1883–84 und 1900

Einträge der Berner Adressbücher, maschinell gelesen. Quelle für
[Vernetzte Schweiz 1860–1914](https://thodel.github.io/vernetzte-schweiz/), wo sie mit den
Telefonbüchern und den anderen Adressbüchern verknüpft werden. Die frühen Berner Adressbücher
(1795–1839) liegen in [adressbuecher-bern-frueh](https://thodel.github.io/adressbuecher-bern-frueh/).

| Band | Seiten | Einwohner | Berufsregister |
|---|---:|---:|---:|
| Adressbuch der Stadt Bern 1883–84 | 335 | 8 241 (S. 83–192) | 4 226 (S. 193–246) |
| Adressbuch der Stadt Bern 1900 | 677 | 15 182 (S. 142–385) | 7 094 (S. 386–491) |

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

- `data/csv/04_entries.csv`: Einwohnerverzeichnisse.
- `data/csv/04_berufe.csv`: Berufsregister (1900 mit den patentierten Berufen, Gasthöfen und
  Wirtschaften); der Beruf steht in `heading`.
- `data/csv/03_sections.csv`, `data/csv/00_volumes.csv`: Seitenbereiche und Bände (mit Prüfsumme des PDFs).
- `data/csv/10_authority_links.csv`: leer; Normdaten verknüpft «Vernetzte Schweiz» über die Personen.
- `data/qwen/<Jahr>/`: die Lesung, wie sie vom Modell kam.

`python scripts/convert.py` erzeugt `data/csv/` aus `data/qwen/`; `python -m unittest discover -s tests`.

## Wie gelesen

- **Modell:** `qwen3.8-27b` auf GPUStack der Universität Bern, Seitenbild 2× vergrössert, Ausgabe als
  JSON-Zeilen. Vorlage sind die PDFs von e-rara (700–1000 px breite Bilder).
- **Stichprobe, von Hand am Seitenbild:** 1883–84 61 von 73 Einträgen voll korrekt (84 %), 1900 121 von
  146 (83 %). Die Fehler sind meist einzelne Buchstaben in Namen und Strassen.
- Keine Nachkorrektur; `qa_flags` markiert Verdachtsfälle.

## Nicht übernommen

Behörden, Vereine, Häuser- und Eigentümerverzeichnisse (1883–84 S. 247–277, 1900 S. 492–544), Stadtplan,
Tarife, Inserate. Das Heft «Die Häuser-Nummerirung in Bern» (1882) ist gelesen, aber noch nicht hier.
Der Band 1860 (Fraktur) ist nicht ganz gelesen: in der Probe waren nur 40–60 % der Einträge korrekt.

## Lizenz

Die Bücher sind vor 1914 erschienen; ihr Inhalt ist gemeinfrei (URG Art. 2 Abs. 1, Art. 29 Abs. 2).
Die Daten in `data/` stehen unter [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), der Code
unter MIT. Die Scans liegen nicht in diesem Repo. `ref/bernhist/` enthält Einzelwerte aus BERNHIST und
steht wie BERNHIST unter der MIT-Lizenz (© 2019 Universität Bern, Universitätsbibliothek; `ref/bernhist/LICENSE`).
