# Werte aus BERNHIST

`werte.csv` enthält die Einzelwerte aus BERNHIST (Historisch-statistische Datenbank des Kantons Bern,
Projekt Christian Pfister, heute bei der Universitätsbibliothek Bern, https://www.bernhist.ch), die
`scripts/85_abdeckung.py` als Nenner braucht: je Zeile Ort, Thema, Jahr, Wert und die Nummer des Werts
im Dump (`data_entry_id`). Alle Werte gelten für die Einwohnergemeinde Bern (Ort 457).

- Quelle ist der Dump im Repo `ub-unibe-ch/bernhist` (Stand 22.03.2024), lokal in SQLite geladen. Der Dump
  selbst liegt nicht hier. `python scripts/85_abdeckung.py --bernhist <sqlite>` liest die Werte neu aus.
- **Lizenz: MIT.** Das Repo `ub-unibe-ch/bernhist` mit dem Dump `data.sql.gz` steht unter der MIT-Lizenz,
  Copyright (c) 2019 Universität Bern, Universitätsbibliothek. Die Werte hier übernehmen diese Lizenz; der
  Lizenztext liegt in `LICENSE` und muss bei einer Weitergabe mitgehen. Die MIT-Lizenz spricht von «Software»;
  der Dump ist Teil desselben Repos, eine eigene Lizenz für die Daten nennen weder das Repo noch bernhist.ch.
  Dieser Ordner fällt deshalb nicht unter die CC0-Freigabe von `data/`.
- Zitieren: BERNHIST, Historisch-statistische Datenbank des Kantons Bern, Universitätsbibliothek Bern,
  https://www.bernhist.ch, Daten aus https://github.com/ub-unibe-ch/bernhist (Stand 22.03.2024). Zur Anlage:
  Christian Pfister und Niklaus Schranz, BERNHIST – Plattform für fächerübergreifendes Forschen und Lehren in
  Raum und Zeit, in: Itinera 17 (1995), 46–78; zu den Quellen: Christian Pfister, Im Strom der Modernisierung.
  Bevölkerung, Wirtschaft und Umwelt im Kanton Bern 1700–1914, Bern 1995.
- Für 1856 und 1910 führt BERNHIST die Erwerbstätigen in zwei Reihen. 1856 wird die Reihe mit allen drei
  Sektoren verwendet (11 701; die andere steht als `erw_1856_stellung`, 11 163, nach Stellung im Beruf). 1910
  wird die Reihe im Gebietsstand von 1910 verwendet (35 250, mit Frauen und Männern, ohne Bümpliz wie die
  Bevölkerung); sie hat keinen 3. Sektor, das Skript rechnet ihn als Rest. Die andere Reihe (37 247) zählt
  Bümpliz mit.
