# Adressbücher der Stadt Bern 1883–84 und 1900

Einträge der Berner Adressbücher, maschinell gelesen. Quelle für
[Vernetzte Schweiz 1860–1914](https://thodel.github.io/vernetzte-schweiz/), wo sie mit den
Telefonbüchern und den anderen Adressbüchern verknüpft werden. Die frühen Berner Adressbücher
(1795–1839) liegen in [adressbuecher-bern-frueh](https://thodel.github.io/adressbuecher-bern-frueh/).

| Band | Seiten | Einwohner | Berufsregister |
|---|---:|---:|---:|
| Adressbuch der Stadt Bern 1883–84 | 335 | 8 241 (S. 83–192) | 4 226 (S. 193–246) |
| Adressbuch der Stadt Bern 1900 | 677 | 15 182 (S. 142–385) | 7 094 (S. 386–491) |

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
unter MIT. Die Scans liegen nicht in diesem Repo.
