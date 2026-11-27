# Auftrag: gelesene Berner Bände übernehmen

Anleitung für den geplanten Claude-Auftrag «Bern: gelesene Bände übernehmen» (alle 4 Stunden). Er setzt
die Läufe fort, die `README.md` beschreibt: auf tei liest `be_weekly.py` Strom A (Antiqua 1881–1914, qwen3.8)
und `be_gemini.py` Strom B (Fraktur 1861–1879, Gemini).
Zeiten in MEZ. Nie einen Schlüssel ausgeben.

## Regeln

- Arbeiten in `~/Repos/adressbuecher-bern` (vorher `git pull --ff-only`). Hat der Checkout fremde,
  nicht committete Änderungen, nichts anfassen: in der Statusdatei melden und enden.
- Committen nur mit Pfad, nie `git add -A`. Vor jedem Push den Stand in einem sauberen Klon prüfen
  (Tests, Skripte importierbar, `90_seite.py` baut). Vor dem Push `git pull --rebase`.
- `data/csv/*` nur über `scripts/convert.py` ändern, `data/qwen/<Band>/` (Strom A) und `data/gemini/<Band>/`
  (Strom B) nur mit dem Ergebnis von tei.
- Keine Seitenbilder und keine PDFs ins Repo; die Seite verlinkt die Bilder über IIIF bei e-rara (PDM).
- Höchstens zwei Bände je Lauf, älteste zuerst.
- **Zurückgestellt, nicht übernehmen ohne Entscheid von Tobias** (Stichprobe unter 80 %, 26.11.2026): 1864 (63/80;
  Bild 213, die letzte Seite des Berufsregisters, am 27.11.2026 nachgelesen). In `scripts/convert.py` steht seine SECTIONS-Zeile
  auskommentiert. Diesen Band nur melden, nicht als «zu übernehmen» zählen. (1867 nach 66/80 übernommen.)
- Einen Band nicht übernehmen, wenn die Seitenbereiche nicht stimmen, die Stichprobe unter 80 % voll
  korrekter Einträge liegt oder die Tests rot sind: melden und weiter.

## Schritte

1. **Stand holen**, beide Ströme:
   `ssh dh@tei.dh.unibe.ch 'cd /home/dh/adressbuch_qwen/weekly_bern && python3 be_weekly.py --status && python3 be_gemini.py --status'`.
   Zu übernehmen sind Bände mit Status `gelesen`, die nicht in `scripts/weekly/ingested.csv` stehen, aus
   beiden Strömen zusammen nach Jahr (Strom B ist älter und kommt damit zuerst). Steht bei Strom B ein Band
   auf `angehalten: …` (Kostenschutz), das melden; nicht mit `--resume` weiterlaufen lassen. Bände
   mit `fehler: …` melden. Gibt es nichts zu tun: eine Zeile in die Statusdatei (Zeit, laufender Band, Stand)
   und enden. Ist tei nicht erreichbar (VPN), ebenso eine Zeile und enden.

2. **Einmalig, vor dem ersten neuen Band: Repo auf viele Bände umstellen.** Eigener Commit, eigener Push.
   - Bisher kennen `90_seite.py` (`VOLUMES`, Platzhalter `__N1883__` …, Bandmenü `#vol`, Texte
     «1883–84 und 1900») und `92_karte.py` (Bandmenü, `['1883', '1900']`) nur die zwei Bände. Beide sollen die
     Bände aus `data/csv/00_volumes.csv` nehmen. Das Bandmenü bleibt absteigend mit dem neuesten Band
     vorgewählt (so war es; `tests/` in adressbuecher-zuerich `test_baende_ordnung.py` zeigt das Muster).
   - `convert.py` schreibt je Band eine Datei (`04_entries_<Band>.csv`, `04_berufe_<Band>.csv`), wie
     adressbuecher-zuerich seit c2eabb4. Zusammen würden die Bände sonst über 100 MB. Alle Leser
     (`80_telefon.py`, `81_baende.py`, `82_normdaten.py`, `85_abdeckung.py`, `90_seite.py`, `92_karte.py`,
     `tests/`) auf die Dateien je Band umstellen.
   - Band-Kennungen sind Zeichenketten: Supplemente heissen `1893s`, `1896s`. Stellen mit `int(volume)`
     (etwa `82_normdaten.py`) mit `int(v[:4])` lesen.
   - Gegenprobe: Für 1883 und 1900 müssen die Einträge vorher und nachher dieselben sein (Zeilen der alten
     `04_entries.csv`/`04_berufe.csv` gegen die neuen Dateien vergleichen) und die Seite gleich viele Zeilen
     zeigen. Live nach dem Deploy prüfen.
   - In Vernetzte Schweiz (`~/Repos/vernetzte-schweiz/config/sources.toml`, Eintrag `bern`) die Dateiliste
     im selben Lauf auf die neuen Pfade setzen (Schritt 4).

3. **Je Band** (Kennung `<Band>`, z. B. `1881`, `1893s`):
   1. Holen: `rsync -rt dh@tei.dh.unibe.ch:/mnt/wbkolleg_dh_1/tei/adressbuch_qwen/full/bern<Band>/{entries.csv,pages.csv} data/<Leser>/<Band>/`
      mit `<Leser>` = `qwen` für Strom A, `gemini` für Strom B; dazu `…/weekly_bern/<Band>/{iiif_pages.csv,classify.csv}`
      nach `/tmp`. Bei Strom B ausserdem die Kosten festhalten: Summe `usd` und Token aus
      `full/bern<Band>/results/*.json` (Feld `usage`), in `ingested.csv` und im Bericht.
   2. **Seitenbereiche** aus `--status` an den Rändern prüfen: je erste und letzte Seite von Einwohnern und
      Berufen über IIIF ansehen (`<iiif_image>/full/900,/0/default.jpg` aus `iiif_pages.csv`). Davor stehen
      meist Behörden, danach Hauseigentümer oder Strassen. Nötigenfalls korrigieren; Einträge ausserhalb der
      Bereiche verwirft `convert.py`.
   3. **convert.py:** `SECTIONS["<Band>"]` ergänzen. Beim ersten Band von Strom B: `convert.py` liest dann
      `data/qwen/` und `data/gemini/` und setzt `parse_method` je Band (`METHOD` gilt bisher für alle:
      «qwen3.8-27b, Bild 2x»; für Strom B «gemini-3.5-flash (Antwort gemini-3.6-flash), IIIF bis 1600 px»).
      Seite, README und Lizenztext nennen den Leser je Band. Seite = Bildnummer in e-rara (Canvas, 1-basiert), anders
      als bei 1883 und 1900, wo die Seite die PDF-Seite ist (PDF-Seite k = Canvas k−1). `python3 scripts/convert.py`,
      `python3 -m unittest discover -s tests`.
   4. **Stichprobe:** 20 zufällige Einträge (Seed = erste vier Ziffern der Kennung) gegen das Seitenbild
      prüfen. Voll korrekt heisst: alle Felder. In `data/review/weekly_<Band>.csv` festhalten. Bekannt aus der
      Probe 1881: das Kürzel «Brunng.» (Brunngasse) liest qwen als «Brunn g.» oder «Brung.»; zählt als Fehler.
      Strom B (Fraktur): besonders auf F/J bei Initialen und auf ü/ä achten (Probe 1861: «Bähler» statt «Bühler»
      erbte sich auf alle Folgeeinträge mit Gedankenstrich). Einen Familiennamen ausserhalb der alphabetischen
      Reihenfolge als Hinweis werten. In `ingested.csv` die Kategorie der Fehler notieren.
   5. **Tabellen und Seite:**
      - `web/erara_pages.csv` um den Band ergänzen: `pdf_page` = Canvas-Nummer aus `iiif_pages.csv`,
        `erara_titleinfo` = `erara_id` aus `queue.csv`, `canvas_id` = letzte Zahl von `iiif_image`,
        `canvas_label` = `label`, `image` = `iiif_image`;
      - `data/csv/00_volumes.csv` um den Band ergänzen (Titel aus `queue.csv`, ohne PDF und Prüfsumme,
        `pages` = Zahl der Canvases, `covers` = Bern);
      - README-Tabelle und die Texte zur Stichprobe ergänzen;
      - dann `10_geo.py`, `80_telefon.py`, `81_baende.py`, `82_normdaten.py`, `85_abdeckung.py` (nur
        wenn BERNHIST-Werte für das Jahr da sind), `90_seite.py`, `92_karte.py`.
   6. Commit `Bern <Band> (e-rara <erara_id>): Einwohner n, Berufsregister m` mit Pfaden, sauberer Klon, Push.
   7. In `scripts/weekly/ingested.csv` eintragen (`volume,date,commit,entries,berufe,sample,note`; bei Strom B
      in `note` Leser und Kosten, z. B. «gemini, 106 S., 4.88 $»).

4. **Vernetzte Schweiz** (einmal je Lauf, nach allen Bänden; alle Bände 1881–1914 liegen im Zeitfenster):
   1. In `config/sources.toml` beim Eintrag `bern` den Commit heben und die Dateien je Band aufführen.
   2. `make ingest link entities`; dann `python3 scripts/hls_coverage.py`, `scripts/elites_match.py`,
      `python3 scripts/check_migration.py --update`. Zahlen in PLAN.md, README und docs nachführen. Neue Texte
      in alle drei i18n-Dateien (de/fr/en).
   3. `python3 -m unittest discover -s tests`, Commit mit Pfaden, sauberer Klon, Push.
   4. Im Berner Repo `80_telefon.py`, `81_baende.py`, `82_normdaten.py` mit dem neuen Commit von Vernetzte
      Schweiz laufen lassen, committen, pushen; in `ingested.csv` vermerken.
   5. Auf beide Pages-Deploys warten und live prüfen: Suche im neuen Band, Link auf e-rara, eine Einheit in
      Vernetzte Schweiz.
   Gelingt Schritt 4 nicht, den Band trotzdem im Berner Repo lassen und in `ingested.csv` «Vernetzte Schweiz
   steht aus» vermerken; der nächste Lauf holt es nach.

5. **Bericht** (kurz, deutsch, MEZ): übernommene Bände mit Einträgen und Stichprobe, Commits, offene Punkte,
   nächster Band auf tei. Denselben Text in
   `~/Library/Application Support/Claude/side-session-notes/local_05d0e445-92c3-423f-94b6-d1c32b9eaa4c/bern_weekly_status.md`
   oben einfügen (Datei anlegen, falls sie fehlt).
