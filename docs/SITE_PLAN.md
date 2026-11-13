# Plan: Seite für die Adressbücher Bern 1883–84 und 1900

Stand 13.11.2026. Vorlage ist die Seite von Baden (https://thodel.github.io/adressbuecher-baden/,
`scripts/90_seite.py`, `.github/workflows/pages.yml` in thodel/adressbuecher-baden): eine statische Seite,
die GitHub Actions aus `data/csv/` baut. Sie hat Reiter, Suche, Filter, Flagging je Zeile und eine
Hinweisbox zur maschinellen Lesung, im Aussehen von Aarau und Basel.

`data/csv`, `data/qwen` und `scripts/convert.py` bleiben für die Seite unberührt, weil Vernetzte Schweiz
diese Daten per Commit pinnt. Neue Konvertierungen (Punkt 4) brauchen einen neuen Pin.

## Umfang

34 753 Zeilen: 1883–84 hat 8 241 Einwohner und 4 226 Einträge im Berufsregister, 1900 hat 15 182 und
7 094. Alles in die Seite eingebettet wären es rund 6–7 MB, ähnlich wie bei Aarau. Besser ist JSON je
Band als eigene Datei (`_site/data/1883.json`, `1900.json`): 1900 wird zuerst geladen, 1883–84 beim
Bandwechsel nachgeladen.

## Was die Seite zeigt

1. **Reiter Einwohner und Berufsregister** wie bei Baden. Den Gemeindefilter gibt es nicht, weil die
   Gemeinde immer «Bern» ist. Stattdessen gibt es einen Filter **Strasse** (Auswahl mit Anzahl) und
   einen Filter **Bezirk**, wo `district` gefüllt ist (die Spalte steht in `data/qwen/1900/entries.csv`).
2. **Seitenbilder, verlinkt.** Die Scans sind auf e-rara öffentlich (Reihe e-rara-4614):
   - 1883–84 hat titleinfo 1396077, 1900 hat titleinfo 1704646.
   - Die IIIF-Manifeste (`https://www.e-rara.ch/i3f/v20/<id>/manifest`) haben 334 bzw. 676 Canvases. Das
     PDF hat eine Seite mehr (Deckblatt), also ist PDF-Seite k gleich Canvas k−1.
   - Link je Zeile: `https://www.e-rara.ch/bes_1/periodical/pageview/<canvas-id>` (geprüft).
   - Die Canvas-IDs einmal aus dem Manifest holen und als Tabelle im Repo ablegen (`web/erara_pages.csv`),
     damit der Bau auf GitHub Actions nicht von e-rara abhängt.
3. **Verortung über die Häuser-Nummerirung 1882.** Die Tabelle «alte Quartiernummer → neue
   Strassennummer» ist in adressbuecher-bern-frueh schon gelesen und verortet
   (`data/csv/07_hausnummern_1882.csv`, 3 831 Zeilen mit Strasse, neuer Nummer und Koordinaten).
   - Die Bände 1883–84 und 1900 haben schon die neuen Nummern. Jeder Eintrag mit Strasse und Nummer lässt
     sich darum direkt verorten. Daraus entstehen eine **Karte** (wie `karte.html` bei Aarau) und je Zeile
     ein Link «dasselbe Haus in den frühen Adressbüchern (alte Nummer)».
   - Die Tabelle in `web/` kopieren und den Herkunfts-Commit nennen, oder sie zur Bauzeit aus
     bern-frueh zu einem festen Commit holen.
   - Die qwen-Lesung des Hefts (`_qwen_test/full/bern1882hn`) nur heranziehen, um sie mit der Fassung aus
     bern-frueh zu vergleichen.
4. **Häuser- und Eigentümerverzeichnisse** (1883–84 S. 247–277, 1900 S. 492–544) sind gelesen, aber
   nicht konvertiert. Sie würden ein Reiter «Häuser» (Strasse, Nr., Eigentümer) wie «Gebäude» bei Aarau.
   Das ist eine Datenänderung (`05_buildings.csv`) und braucht darum einen neuen Pin in Vernetzte Schweiz.
5. **Hinweisbox:** Die Lesung ist maschinell (qwen3.8) und nicht nachkorrigiert. In der Stichprobe waren
   84 % (1883–84) bzw. 83 % (1900) der Einträge voll korrekt, deutlich weniger als bei Baden, weil die
   e-rara-PDFs nur 700–1000 px breit sind. Das offen sagen. Der Band 1860 (Fraktur) ist nicht gelesen.

## Verhältnis zu den frühen Berner Adressbüchern

Nicht zusammenlegen mit https://thodel.github.io/adressbuecher-bern-frueh/ (1795–1848). Die beiden
unterscheiden sich in Lesung (Gemini vs. qwen), Schema und Pflege, und Vernetzte Schweiz pinnt sie
getrennt. Stattdessen:
- gegenseitig verlinken (Navigation «Bern 1795–1848» ↔ «Bern 1883–1900»);
- dasselbe Aussehen;
- der Hausnummern-Link aus Punkt 3 als inhaltliche Brücke.

## Aufwand

- Grundseite mit e-rara-Links und Nachladen je Band: 2–3 h.
- Karte über die Tabelle von 1882: weitere 2–3 h.
- Reiter Häuser (Konvertierung, Prüfung, neuer Pin): weitere 3–4 h.

Das Baden-Skript lohnt sich ab der zweiten Stadt als gemeinsamer Generator, konfiguriert je Stadt mit
Reitern, Spalten, Filtern, Sprache und Bildlink-Muster.
