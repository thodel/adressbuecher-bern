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

## Noch nicht eingerichtet

Den Lauf auf tei gibt es noch nicht. Der cron dort liest bis auf Weiteres das Zürcher Fenster 1900–1920
(`adressbuecher-zuerich/scripts/weekly`). Bern kommt als Nächstes dran: Der Leser für Strom A ist
`zh_weekly.py` mit e-rara statt ZOP, der für Strom B `02d_llm_pages.py` aus adressbuecher-aarau mit einer
Berner Anweisung.
