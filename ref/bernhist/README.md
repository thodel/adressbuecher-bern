# Werte aus BERNHIST

`werte.csv` enthält die Einzelwerte aus BERNHIST (Historisch-statistische Datenbank des Kantons Bern,
Projekt Christian Pfister, heute bei der Universitätsbibliothek Bern, https://www.bernhist.ch), die
`scripts/85_abdeckung.py` als Nenner braucht: je Zeile Ort, Thema, Jahr, Wert und die Nummer des Werts
im Dump (`data_entry_id`). Alle Werte gelten für die Einwohnergemeinde Bern (Ort 457).

- Quelle ist der Dump im Repo `ub-unibe-ch/bernhist` (Stand 22.03.2024), lokal in SQLite geladen. Der Dump
  selbst liegt nicht hier. `python scripts/85_abdeckung.py --bernhist <sqlite>` liest die Werte neu aus.
- Die Nutzungsrechte an den BERNHIST-Daten sind nicht ausgewiesen. Dieser Ordner steht deshalb **nicht**
  unter der CC0-Freigabe von `data/`; er enthält nur, was zum Nachrechnen nötig ist.
- Für 1856 und 1910 führt BERNHIST die Erwerbstätigen in zwei Reihen. Verwendet wird jeweils die Reihe
  mit allen drei Sektoren (1856: 11 701, 1910: 37 247); die andere steht als `erw_1856_stellung`
  (11 163, nach Stellung im Beruf) und `erw_1910_reihe_a` (35 250, mit Frauen und Männern) in der Tabelle.
