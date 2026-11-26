# Warteschlange: Bern 1861–1914

Die Reihe «Adressbuch der Stadt Bern» liegt fast vollständig auf e-rara
([doi:10.3931/e-rara-4614](https://doi.org/10.3931/e-rara-4614), Universitätsbibliothek Bern, Public Domain Mark).
Hier eingebunden sind 1883–84 und 1900. Die übrigen 37 Bände von 1861 bis 1914 stehen in `queue.csv`:

| Strom | Bände | Schrift | Leser | Bilder |
|---|---|---|---|---:|
| A | 1881, 1886–87, 1888–89, 1891–92, 1893–94 (+ Supplement), 1895–96, Supplement 1896–97, 1897–98, 1899, 1901–02 bis 1912–13 (jährlich), 1914 | Antiqua | qwen3.8 (tei) | 14 106 |
| B | 1861–1866, 1867–68, 1868–69, 1870, 1871, 1873, 1875, 1877, 1879 | Fraktur | Gemini | 5 179 |

Zuerst Strom A, dann B, je aufsteigend. Strom A geht wie die Zürcher Bände (`run_qwen.py` auf tei, Seiten über
IIIF). Strom B liest Gemini wie die frühen Berner und Aarauer Bände; qwen las die Fraktur von 1860 in der
Probe nur zu 40–60 % richtig.

- `erara_liste.csv`: e-rara-ID und Titel je Band. Die IDs stammen aus der Bandliste der Reihe auf e-rara
  (Recherche 25.11.2026). Jedes Manifest ist am 25.11.2026 abgerufen und geprüft.
- `make_queue.py`: macht daraus `queue.csv`. Es holt dazu je Band das IIIF-Manifest
  (`https://www.e-rara.ch/i3f/v20/<ID>/manifest`) und liest daraus die Zahl der Bilder und die Bildgrösse.
- Band-Kennung: das erste Jahr des Titels («1867-1868» → `1867`, «1912-1913» → `1912`).
  Supplemente bekommen ein `s` (`1893s`, `1896s`).
- Schrift: bis 1879 Fraktur, ab 1881 Antiqua. Geprüft an Seiten aus 1861, 1877 und 1879 sowie aus 1881,
  1886–87 und 1899.

## Lücken in der Reihe

Kein Band deckt nach der Bandliste auf e-rara die Jahre 1872, 1874, 1876, 1878, 1880, 1885 und 1890 ab. 1882 gibt es nur
«Die Häuser-Nummerirung in Bern». 1913 steckt im Band 1912–13. Die Bandliste stammt aus der Recherche vom 25.11.2026
und ist nicht Band für Band nachgezählt. Ob die Lücken wirklich nicht erschienen
sind oder nur nicht digitalisiert wurden, ist offen. 1859 («Hand- und Adressbuch der Bundesstadt Bern»,
doi:10.3931/e-rara-7083) ist ein eigener Titel und steht nicht in der Warteschlange.

## Lauf auf tei (Strom A)

Seit 25.11.2026 liest `be_weekly.py` auf tei die Bände von Strom A, einen nach dem anderen, in der
Reihenfolge von `queue.csv` (Kopie mit `queue.csv` in `tei:/home/dh/adressbuch_qwen/weekly_bern/`, cron
stündlich um :45, `crontab.txt`). Er beginnt keinen Band, solange `run_qwen.py` oder der Zürcher Lauf
`zh_weekly.py` läuft: Das Zürcher Fenster 1900–1920 geht vor. Umgekehrt wartet `zh_weekly.py`, solange
`be_weekly.py` liest. Je Band:

1. Manifest bei e-rara holen, Seitentabelle schreiben (`weekly_bern/<Band>/iiif_pages.csv`).
2. Jede Seite zuordnen (Bild 600 px breit, qwen3.8 nennt den Teil). Der grösste Block ergibt die
   Seitenbereiche Einwohner und Berufe.
3. Diese Seiten über IIIF holen (halbe Breite des Scans, mindestens 1100, höchstens 1200 px), mit `run_qwen.py` lesen
   (2× vergrössert, zwei Durchgänge), mit `collect.py` sammeln.
4. Ergebnis auf den Forschungsspeicher (`/mnt/wbkolleg_dh_1/tei/adressbuch_qwen/full/bern<Band>/`, Zuordnung
   unter `weekly_bern/<Band>/`), Seitenbilder löschen.

Stand: `python3 be_weekly.py --status` (`state.json`, Protokoll `weekly.log`). Einen Band einzeln lesen,
auch neben Zürich: `python3 be_weekly.py --only 1881`.

Probe 1881 (25.11.2026): Die Zuordnung ergab Einwohner S. 80–193 und Berufe S. 194–249; an den Seitenbildern
geprüft, beide Grenzen stimmen (davor Behörden, danach Hauseigentümer). Leseprobe S. 120 (Einwohner) in 800 und
1100 px: 80 von 93 Einträgen gleich; von den übrigen war am Seitenbild 1100 px öfter richtig
(Sonnegg, Gerechtigkeitsgasse 88, Schwarzthorstr.), daher mindestens 1100 px. Beide lasen «Brunng.»
falsch («Brunn g.» bzw. «Brung.»): bei der Übernahme prüfen. S. 210 (Berufe, 800 px): die ersten 10 Einträge
wortgenau.

## Übernahme und Offenes

- Übernahme ins Repo: Der geplante Claude-Auftrag «Bern: gelesene Bände übernehmen» (alle 4 Stunden) folgt
  [TASK.md](TASK.md) und trägt jeden Band in `ingested.csv` ein. Vor dem ersten Band stellt er das Repo auf
  eine Datei je Band und Bandlisten aus `00_volumes.csv` um.
- Strom B: siehe unten.

## Lauf auf tei (Strom B, Fraktur, Gemini)

`be_gemini.py` liest die 14 Fraktur-Bände 1861–1879 mit `gemini-3.5-flash`, aufsteigend, als
systemd-Einheit `bern-gemini` auf tei (unabhängig vom Laptop; Gemini teilt sich die GPU nicht mit Zürich).
Die Seitenzuordnung macht wie in Strom A qwen3.8 (nur der Teil einer Seite, kostenlos); Gemini liest nur
die Seiten der Einwohner- und Berufsteile, Bild über IIIF in der Breite des Scans (höchstens 1600 px).
Je Seite steht die vollständige `usageMetadata` (Eingabe-, Ausgabe- und Denk-Token) und der Preis in $ in
`full/bern<Band>/results/*.json`, nach dem Listenpreis $1.50 / $9.00 je Mio. Token (Denken = Ausgabe).

Schutz: Ab der 20. Seite hält der Lauf an, wenn die Seiten im Mittel mehr als 0,08 $ kosten oder Strom B
zusammen mehr als 350 $; ebenso bei einer Ablehnung der API. Weiter nach Prüfung mit `--resume`.
Stand: `python3 be_gemini.py --status` (`gemini_state.json`, Protokoll `gemini.log`).

Probe 1861 (26.11.2026): Seitenbereiche Einwohner S. 79–145, Berufe 146–184, am Bild bestätigt. 20 Seiten, alle
sauber beendet, 1 229 Einträge, 0,046 $ je Seite (1 753 Eingabe-, im Mittel 4 900 Ausgabe-Token, keine
Denk-Token gemeldet; Antwort von `gemini-3.6-flash` unter dem Namen `gemini-3.5-flash`). Am Bild: S. 81 15 von
17 Einträgen richtig, beide Fehler F statt J gelesen; S. 87 «Bühler» als «Bähler», was alle Folgeeinträge
mit Gedankenstrich erbt. Die Anweisung hat seither eine Regel zu F/J und zu Umlauten; damit las S. 87 «Bühler»
und S. 81 «Baldesperger F.» richtig. F und J bleiben an einzelnen Stellen unsicher. Strom B betrifft etwa
2 300 Seiten der Teile Einwohner und Berufe (von 5 179 Bildern), also rund 110 $.
