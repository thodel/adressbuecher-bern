# Abdeckung der Adressbücher 1883–84 und 1900, gemessen an BERNHIST

Stand 23.11.2026. Die Frage: Welchen Teil der Stadt Bern bilden die beiden maschinell gelesenen Adressbücher ab,
und welche Gruppen stehen fast vollständig darin, welche kaum? Die Nenner kommen aus BERNHIST (Stadt Bern,
Ort 457), die Zähler aus `data/csv/04_entries_<Band>.csv` und `04_berufe_<Band>.csv`.

Nachrechnen: `python scripts/85_abdeckung.py` schreibt `data/abdeckung/abdeckung.csv`, `sektoren.csv` und
`wachstum.csv` und ersetzt den Tabellenblock unten. Die verwendeten BERNHIST-Werte stehen in
`ref/bernhist/werte.csv`; mit `--bernhist <sqlite>` oder der Umgebungsvariable `BERNHIST_SQLITE` liest das
Skript sie neu aus dem Dump. Tests: `python -m unittest discover -s tests`.

## Befund in Kürze

- **Rund ein Fünftel der Bevölkerung, aber fast jeder Haushalt.** 1883–84 stehen 7 969 Personen im
  Einwohnerverzeichnis, das sind 18,0 % der Wohnbevölkerung und 83 Personen je 100 Haushalte. 1900 sind es
  14 184 Personen, 22,1 % der Bevölkerung und 102 je 100 Haushalte. Das Buch nennt Erwachsene mit eigener
  Adresse, keine Köpfe; der Anteil an den Haushalten ist die aussagekräftigere Zahl.
- **Das Buch wächst schneller als die Stadt.** Von 1883 bis 1900 wächst die Bevölkerung um 2,2 % im Jahr, die
  Zahl der Personen im Einwohnerverzeichnis um 3,5 %. Der Band 1900 erfasst also einen grösseren Teil der
  Stadt als der Band 1883–84. Das Berufsregister wächst mit 2,8 % (Einheiten) nur wenig schneller als die Stadt.
- **Fast vollständig** sind 1900 die Gruppen, die ein Gewerbe, ein Amt oder eine Praxis haben: Ärzte (83 mit
  der Berufsangabe «Arzt» bei 92 bis 103 erwarteten; mit allen «Dr. med.» 121), Lehrerinnen und Lehrer der
  Primarschulen (143 bei rund 149 Lehrpersonen insgesamt), Spezereihandlungen (215 im Berufsregister bei rund 243). Der Band 1883–84
  liegt überall tiefer (Spezereihandlungen 119 bei rund 167).
- **Kaum vorhanden** sind Dienstboten (16 und 24 Einträge bei mehreren Tausend) und Taglöhner (44 und 14).
  Wer im Haushalt des Arbeitgebers wohnt oder keinen festen Erwerb hat, steht nicht im Buch.
- **Frauen** sind stark untervertreten: 1 611 (1883–84) und 3 189 (1900) erkannte Frauen sind 6,6 % und 9,0 %
  der Frauen in der Stadt. Aufgenommen sind sie vor allem als Witwen (425 und 1 217, rund 20 % und 45 % der
  geschätzten Witwen) und mit eigenem Erwerb (Schneiderin, Lehrerin, Wäscherin, Privatière).
- **Nach Sektoren** ist der 3. Sektor (Handel, Verwaltung, Verkehr) übervertreten und der 2. (Gewerbe,
  Industrie) untervertreten: Im Buch von 1900 gehören 55 % der Personen mit Sektor zum 3. und 43 % zum 2.,
  in der Volkszählung 1910 sind es je 49 %. Gemessen an den geschätzten Erwerbstätigen erfasst der
  Band 1900 rund die Hälfte des 3. Sektors, 39 % des 2. und 42 % des 1.

## Wen die Verzeichnisse nennen

**Einwohnerverzeichnis.** Alphabetisch nach Familienname, je Zeile eine Person oder eine Einheit mit Beruf und
Adresse. Die Bände sagen nicht, wer aufgenommen wurde (ein Vorwort mit Regeln ist nicht gelesen worden); der
Befund aus den Daten:

- Zum grössten Teil sind es Männer mit Beruf, also Haushaltsvorstände und Gewerbetreibende. Daneben stehen aber
  auch Abhängige mit eigener Adresse: 612 (1883–84) und 1 323 (1900) Personen sind Gesellen, Commis,
  Angestellte oder Arbeiter, 150 und 52 nennen ihren Arbeitgeber («Schneider bei Hrn. Bloch»). Das
  Verzeichnis ist deshalb etwas mehr als eine Liste der Haushaltsvorstände, und 1900 kommt auf 100 Haushalte
  mehr als eine genannte Person.
- Frauen stehen mit eigenem Eintrag, wenn sie Witwe sind («Wwe.», «Wittwe», oft mit dem Beruf des Mannes:
  «des Schusters Wwe.»), ledig mit eigenem Erwerb oder Vermögen («Frl.», «Jgfr.», «Privatière») oder ein
  Gewerbe führen («Frau», Kostgeberei, Spezereihandlung). Ehefrauen erscheinen nur im Allianznamen des Mannes
  («Krebs-Gugelmann»).
- Firmen stehen im selben Alphabet (151 und 262 Personenfirmen mit «&», «Cie.», «Gebr.», «Söhne», «Erben»),
  ebenso Ämter, Vereine und Betriebe ohne Personenname (96 und 453). Der Band 1900 enthält dazu 283 Verweise
  («Rüdt, s. auch Rüd»), die keine Einträge sind.
- Die Spalte `entry_type` der CSV taugt für diese Trennung nicht: Ihr Muster trifft auch Personen, in deren
  Adresse «Gesellschaftsstrasse» oder in deren Beruf «Waffenfabrik» steht. Die Messung bestimmt die Art deshalb
  neu und nur aus den Namensfeldern (`art()` im Skript). Die CSV bleibt unverändert, weil «Vernetzte Schweiz»
  sie per Commit einbindet.
- Kinder, Ehefrauen, Dienstboten im Haushalt, Untermieter ohne eigenen Erwerb und Anstaltsinsassen fehlen.

**Berufsregister.** Nach Rubriken geordnet (392 Rubriken 1883–84, 538 im Jahr 1900), je Zeile ein Name mit
Adresse, meist ohne Beruf, weil die Rubrik ihn nennt. Es ist ein Auszug der Gewerbetreibenden aus dem
Einwohnerverzeichnis und keine zweite Erhebung: 84 % (1883–84) und 88 % (1900) der Zeilen finden sich mit
gleichem Namen im Einwohnerverzeichnis wieder; mit derselben Adresse sind es nur 39 % und 37 %, weil das
Register die Geschäftsadresse nennt und die Abkürzungen der Strassen abweichen. Wer mehrere Gewerbe führt, steht
in mehreren Rubriken; 4 226 und 7 094 Zeilen sind 3 880 und 6 240 verschiedene Namen mit Adresse. Unselbständige
fehlen im Register ganz. Der Band 1900 enthält dazu die patentierten Berufe (Ärzte, Zahnärzte, Hebammen),
Gasthöfe und Wirtschaften; 1883–84 gibt es keine Rubrik «Aerzte».

## Nenner aus BERNHIST

BERNHIST hat für die Stadt Bern die Wohnbevölkerung zu den Volkszählungen (1880: 43 197, 1888: 46 009,
1900: 64 227, 1910: 85 651), die Haushalte 1888 (9 931), aber die Berufsstruktur nur 1856 und 1910. Daraus
folgt, wie die Nenner gebildet sind:

| Nenner | 1883–84 | 1900 | Art |
|---|---|---|---|
| Wohnbevölkerung | 44 252 | 64 227 | 1883: linear zwischen 1880 und 1888; 1900: Volkszählung |
| Haushalte | 9 552 | 13 863 | geschätzt: Bevölkerung durch die Haushaltsgrösse von 1888 (4,63 Personen) |
| Erwerbstätige | 18 924 | 26 816 | geschätzt: Bevölkerung mal Erwerbsquote, zwischen 1856 (44,4 %) und 1910 (41,2 %) interpoliert |
| Erwerbstätige je Sektor | | | geschätzt: Erwerbstätige mal Anteil des Sektors 1910 (1,9 %, 49,0 %, 49,1 %; Erwerbstätige 1910 im Gebietsstand von 1910, ohne Bümpliz: 35 250, der 3. Sektor als Rest) |
| Frauen | 24 331 | 35 316 | geschätzt: Frauenanteil 1856 und 1930 je 55,0 %; dazwischen fehlt das Geschlecht |
| Witwen | 2 090 | 2 721 | geschätzt: Anteil der Verwitweten 1856 (7,3 %) und 1910 (5,3 %) interpoliert, davon Frauen wie 1846 (75 %) |
| Erwerbstätige Frauen | 5 750 | 8 147 | geschätzt: Erwerbstätige mal Frauenanteil 1910 (30,4 %) |
| Selbständige | 6 151 | 8 068 | geschätzt: Anteil an der Bevölkerung 1856 (16,0 %) und 1930 (10,2 %) interpoliert |
| Ärzte | 82 / 69 | 103 / 92 | 1856: 47, 1910: 116; erste Zahl linear, zweite über die Ärztedichte |
| Lehrer und Lehrerinnen | 102 | 149 | 1895: 131 bei 5 151 Schülern (öffentliche Schulen, mehrheitlich Primarstufe), mit der Bevölkerung umgerechnet |
| Spezereigeschäfte | 167 | 243 | 1901: 251, mit der Bevölkerung umgerechnet |
| Dienstboten | 5 061 | 7 346 | 1856: 3 016 (11,4 % der Bevölkerung), mit der Bevölkerung umgerechnet |
| Taglöhner | 2 794 | 4 055 | 1856: 1 665 (6,3 %), mit der Bevölkerung umgerechnet |

«Geschätzt» heisst: BERNHIST hat für das Bandjahr keinen Wert, und die Zahl ruht auf einer Annahme, die in
`abdeckung.csv` in der Spalte `nenner_herleitung` steht. Der Band 1883–84 gibt den Stand von 1883 wieder und ist auf 1883 gerechnet (bestätigt von Tobias Hodel); mit 1884
wäre die Bevölkerung um rund 350 Personen grösser und die Quote um 0,1 Prozentpunkte kleiner.

## Zähler

- **Art des Eintrags** (`art()`): Person, Firma, Institution oder Verweis, aus Name und Vorname bestimmt.
- **Frauen** (`frau()`): Witwe, Fräulein, Frau nach der Standesangabe; sonst «weiblich», wenn der ausgeschriebene
  Vorname oder die Berufsform (-in, -ière, Modiste, Hebamme) es zeigt. Viele Vornamen sind abgekürzt («M.»,
  «El.»); die Zahl der Frauen ist darum eine Untergrenze.
- **Sektor** (`sektor()`): aus der ersten Berufsangabe bis zum ersten Komma, mit Wortlisten je Sektor. Die
  Einteilung folgt BERNHIST für 1910: Der 2. Sektor enthält Bau-, Nahrungsmittel-, Bekleidungs- und
  Reinigungsgewerbe (auch Coiffeur, Wäscherin, Glätterin) und den Druck; der 3. Handel, Banken, Gastgewerbe,
  Verkehr (Post, Bahn, Fuhrwesen), Verwaltung, Schule, Kirche, Gesundheit und persönliche Dienste; der 1.
  Landwirtschaft, Gärtnerei und Forst (auch Holzhauer). Stehen mehrere Berufe da, gilt der zuerst genannte.
  «Privatier», «Rentière», «gew. Wirt» und die Witwe «des Schusters» zählen als ohne Erwerb; Taglöhner, Arbeiter
  ohne Betrieb und unlesbare Angaben bleiben ohne Sektor. Fehlt der Beruf, entscheidet der Titel (Dr., Prof.,
  Pfr., Oberst: 3. Sektor).
- **Stichprobe.** 40 Personen je Band mit Berufsangabe, zufällig mit festem Startwert gezogen
  (`data/abdeckung/stichprobe_sektor.csv`), nach dem Festlegen der Regeln. 78 von 80 sind richtig zugeordnet
  (97,5 %); die zwei Fehler sind «Strassensäuberer» (kein Sektor erkannt) und «Vater, Schreiber» (als ohne Erwerb
  gelesen). Fünf weitere sind als Grenzfälle vermerkt, etwa «Angestellter» ohne Branche. Beurteilt hat Claude,
  nicht eine zweite Person, und geprüft ist die Zuordnung der gelesenen Angabe, nicht die Lesung selbst.
- **Einzelne Gruppen** (`gruppe()`): Ärzte ohne Zahn- und Tierärzte, einmal nur nach der Berufsangabe, einmal
  mit allen, die «Dr. med.» im Titel führen (Professoren, Beamte des Gesundheitsamts, Assistenten). Lehrer und
  Lehrerinnen einmal nur dort, wo eine Primarschule genannt ist (1900 meist: «Lehrerin a. d. Mattenschule»;
  1883–84 selten), einmal mit allen, die eine öffentliche Schule nennen (dazu Sekundarschulen, städtisches
  Gymnasium, Progymnasium; ohne Lerberschule bzw. Freies Gymnasium, Neue Mädchenschule und Evangelisches Seminar,
  die privat waren), einmal mit allen «Lehrer(in)» ohne Fach und ohne höhere Schule. Spezereihandlungen nach der
  Rubrik des Berufsregisters und nach der Berufsangabe im Einwohnerverzeichnis.

## Ergebnis

<!-- TABELLEN:START -->
| Gruppe | 1883–84: Buch | Nenner | Quote | 1900: Buch | Nenner | Quote |
|---|---:|---:|---:|---:|---:|---:|
| Einträge im Einwohnerverzeichnis | 8 241 | 44 252 | 18,6 % | 15 182 | 64 227 | 23,6 % |
| Personen je Einwohner | 7 969 | 44 252 | 18,0 % | 14 184 | 64 227 | 22,1 % |
| Personen je Haushalt | 7 969 | 9 552 | 83,4 % | 14 184 | 13 863 | 102,3 % |
| Firmen | 151 | – | – | 262 | – | – |
| Ämter, Vereine, Betriebe | 96 | – | – | 453 | – | – |
| Verweise | 25 | – | – | 283 | – | – |
| Verschiedene Namen | 7 420 | 44 252 | 16,8 % | 13 200 | 64 227 | 20,6 % |
| Frauen | 1 611 | 24 331 | 6,6 % | 3 189 | 35 316 | 9,0 % |
| Witwen | 425 | 2 090 | 20,3 % | 1 217 | 2 721 | 44,7 % |
| Fräulein | 166 | – | – | 399 | – | – |
| Personen mit Erwerb | 6 776 | 18 924 | 35,8 % | 12 303 | 26 816 | 45,9 % |
| Frauen mit Erwerb | 969 | 5 750 | 16,9 % | 1 909 | 8 147 | 23,4 % |
| 1. Sektor | 118 | 363 | 32,5 % | 218 | 514 | 42,4 % |
| 2. Sektor | 2 954 | 9 275 | 31,8 % | 5 132 | 13 143 | 39,0 % |
| 3. Sektor | 3 493 | 9 286 | 37,6 % | 6 651 | 13 158 | 50,5 % |
| Berufsregister: Einheiten | 3 880 | 6 151 | 63,1 % | 6 240 | 8 068 | 77,3 % |
| Berufsregister: im Einwohnerverzeichnis wiedergefunden | 3 535 | 4 222 | 83,7 % | 6 219 | 7 086 | 87,8 % |
| Berufsregister: mit gleicher Adresse wiedergefunden | 1 667 | 4 222 | 39,5 % | 2 625 | 7 086 | 37,0 % |
| Ärzte (Beruf nennt «Arzt») | 21 | 82 | 25,8 % | 83 | 103 | 80,4 % |
| Ärzte (dazu Titel «Dr. med.») | 51 | 82 | 62,6 % | 121 | 103 | 117,2 % |
| Ärzte (dazu Titel «Dr. med.», gegen Ärztedichte) | 51 | 69 | 73,5 % | 121 | 92 | 131,4 % |
| Ärzte (Rubrik im Berufsregister) | – | – | – | 58 | 103 | 56,2 % |
| Lehrer und Lehrerinnen (öffentliche Schule genannt) | 70 | 102 | 68,4 % | 226 | 149 | 152,1 % |
| Lehrer und Lehrerinnen (Primarschule genannt) | 33 | 102 | 32,2 % | 143 | 149 | 96,3 % |
| Lehrer und Lehrerinnen (ohne Fach- und höhere Schulen) | 152 | 102 | 148,5 % | 221 | 149 | 148,8 % |
| Lehrer und Lehrerinnen (alle) | 316 | – | – | 462 | – | – |
| Spezereihandlungen (Rubrik im Berufsregister) | 119 | 167 | 71,1 % | 215 | 243 | 88,5 % |
| Spezereihandlungen (Einwohnerverzeichnis) | 61 | 167 | 36,4 % | 150 | 243 | 61,8 % |
| Dienstboten | 16 | 5 061 | 0,3 % | 24 | 7 346 | 0,3 % |
| Taglöhner und Handlanger | 44 | 2 794 | 1,6 % | 14 | 4 055 | 0,3 % |

Verteilung der Personen nach erster Berufsangabe (Anteile in Prozent der Personen mit Sektor):

| | 1883–84: Personen | Anteil | 1900: Personen | Anteil | BERNHIST 1856 | BERNHIST 1910 |
|---|---:|---:|---:|---:|---:|---:|
| 1. Sektor | 118 | 1,8 | 218 | 1,8 | 45,3 | 1,9 |
| 2. Sektor | 2 954 | 45,0 | 5 132 | 42,8 | 31,7 | 49,0 |
| 3. Sektor | 3 493 | 53,2 | 6 651 | 55,4 | 23,0 | 49,1 |
| Beruf ohne Sektor (Taglöhner, Arbeiter …) | 211 |  | 302 |  |  |  |
| ohne Erwerb (Privatier, «gew.», Witwe des …) | 371 |  | 802 |  |  |  |
| keine Angabe | 822 |  | 1 079 |  |  |  |

Stichprobe zur Sektorzuordnung: 78 von 80 Berufsangaben richtig zugeordnet (97,5 %).

Wachstum 1883 bis 1900:

| Grösse | 1883 | 1900 | Faktor | pro Jahr |
|---|---:|---:|---:|---:|
| Wohnbevölkerung (BERNHIST) | 44 252 | 64 227 | 1,45 | 2,22 % |
| Einträge im Einwohnerverzeichnis | 8 241 | 15 182 | 1,84 | 3,66 % |
| Personen im Einwohnerverzeichnis | 7 969 | 14 184 | 1,78 | 3,45 % |
| erkannte Frauen | 1 611 | 3 189 | 1,98 | 4,1 % |
| Firmen | 151 | 262 | 1,74 | 3,29 % |
| Einträge im Berufsregister | 4 226 | 7 094 | 1,68 | 3,09 % |
| Einheiten im Berufsregister | 3 880 | 6 240 | 1,61 | 2,83 % |
<!-- TABELLEN:ENDE -->

Lesehilfe: «Buch» ist die Zahl der Einträge im Band, «Nenner» der Wert aus BERNHIST für das Bandjahr (siehe
oben), «Quote» der Anteil in Prozent. Eine Quote über 100 % heisst, dass Zähler und Nenner nicht dasselbe
meinen: bei den Haushalten, dass mehr als eine Person je Haushalt genannt ist; bei den Ärzten mit «Dr. med.»,
dass der Titel weiter reicht als der Beruf; bei den Lehrpersonen, dass «Lehrerin» ohne nähere Angabe auch
Privatschulen meint.

## Grenzen

- **Haushaltsvorstände statt Köpfe.** Die Quote an der Bevölkerung (18 % und 22 %) ist eine Untergrenze für
  die Reichweite des Buchs und keine Aussage darüber, wie viele Menschen «fehlen». Die Quote an den Haushalten
  ruht auf einer geschätzten Zahl der Haushalte (Haushaltsgrösse von 1888; 1860 waren es 4,46 Personen).
- **Nenner von 1910 für ein Buch von 1900, von 1856 und 1910 für eines von 1883.** Die Berufsstruktur gibt es
  nur für diese beiden Jahre. Alle Quoten zu Erwerbstätigen, Sektoren, Ärzten, Dienstboten und Taglöhnern
  nehmen an, dass sich die Anteile dazwischen gleichmässig verschoben haben. Für den Band 1883–84 ist das eine
  Überbrückung von 27 Jahren und entsprechend unsicher.
- **Erwerbstätige 1910 ohne Bümpliz (korrigiert 23.11.2026).** BERNHIST führt für 1910 zwei Reihen. Bis zum
  23.11.2026 stand hier die Reihe mit allen drei Sektoren (37 247), die Bümpliz (eingemeindet 1919) mitzählt,
  während die Bevölkerung 1910 (85 651) ohne Bümpliz zählt. Jetzt gilt die Reihe im Gebietsstand von 1910
  (35 250), der 3. Sektor ist der Rest. Die Sektorquoten 1900 ändern sich um 1 bis 2 Punkte, die des 1. Sektors
  stärker (27,5 % → 42,4 %), weil Bümpliz bäuerlich war. Gefunden in `thodel/vernetzte-schweiz`,
  `docs/durchdringung_bern.md`.
- **Die Sektoren von 1856 sind nicht vergleichbar.** BERNHIST weist für die Stadt 1856 im 1. Sektor 45 % der
  Erwerbstätigen aus (5 296 von 11 701). Für eine Stadt ist das nicht plausibel; vermutlich sind Dienstboten und
  Taglöhner dort eingerechnet, geprüft ist das nicht. Die Sektorquoten rechnen darum nur mit der Struktur von 1910.
- **Dienstboten 1910 anders abgegrenzt.** 3 016 Dienstboten 1856 stehen 839 im Jahr 1910 gegenüber, bei
  dreifacher Bevölkerung. Der Wert von 1910 ist eine Untergruppe des 3. Sektors und meint nicht dasselbe. Der
  Nenner für Dienstboten und Taglöhner ist deshalb der Anteil von 1856, auf die spätere Bevölkerung übertragen:
  eine Grössenordnung, keine Zählung. Am Befund ändert das nichts, weil die Bücher nur 16 bis 44 solche
  Einträge haben.
- **Ärzte und Lehrpersonen.** Woher BERNHIST die Zahl der Ärzte nimmt und ob Spital- und Amtsärzte mitzählen,
  ist nicht bekannt. Was die 131 Lehrpersonen von 1895 umfassen, sagt BERNHIST nicht; nach
  Auskunft von Tobias Hodel wohl nicht nur die Primarschule, aber mehrheitlich Lehrpersonen der Primarstufe. Die
  Bücher sprechen eher für eine enge Abgrenzung: 1900 nennen 143 Personen eine Primarschule, 226 eine öffentliche
  Schule überhaupt, bei rund 149 erwarteten Lehrpersonen. Umfasste der Nenner alle öffentlichen Schulen, stünden
  im Buch die Hälfte mehr Lehrpersonen, als es gab. Die Quote der Primarlehrpersonen (96 %) ist darum die
  verlässlichere Zahl; privat Unterrichtende fehlen im Nenner sicher.
- **Stichtage.** Der Band 1900 gibt den Stand von 1899 oder Anfang 1900 wieder, die Volkszählung den vom
  1. Dezember 1900. Bei 2,8 % Wachstum im Jahr ist die Quote des Bands 1900 damit um etwa einen halben
  Prozentpunkt zu tief angesetzt.
- **Lesefehler.** Die Bände sind maschinell gelesen und nicht korrigiert; 84 % und 83 % der Einträge waren in
  der Stichprobe voll korrekt. Zahlen von Einträgen sind davon kaum berührt, Gruppen nach Berufsangabe schon:
  verlesene Berufe («Milchkändler») fängt die Wortliste nur zum Teil, der Rest liegt bei den 211 und 302
  Angaben ohne Sektor. Falsch getrennte Zeilen und fortgeschriebene Familiennamen verschieben die Zahl der
  Firmen und der verschiedenen Namen um einige Dutzend.
- **Frauen und Witwen.** Das Geschlecht ist nur erkennbar, wo Stand, Vorname oder Berufsform es zeigen. Der
  Nenner für Witwen verbindet drei Schätzungen (Bevölkerung, Anteil der Verwitweten, Frauenanteil von 1846).
- **Burger und Einsassen** lassen sich nicht messen: BERNHIST hat die Burger der Stadt für 1888, aber die
  Bände nennen das Burgerrecht nicht (`citizen_flag` ist leer).
- **Lizenz und Zitat.** BERNHIST steht im Repo `ub-unibe-ch/bernhist`, das auch den Dump enthält, unter der
  MIT-Lizenz (© 2019 Universität Bern, Universitätsbibliothek). Die verwendeten Einzelwerte liegen mit Ort, Thema,
  Jahr und Quelle in `ref/bernhist/werte.csv` und übernehmen diese Lizenz (`ref/bernhist/LICENSE`), ausserhalb der
  CC0-Freigabe von `data/`. Die MIT-Lizenz nennt «Software»; eine eigene Datenlizenz gibt es nicht. Zitieren:
  BERNHIST, Universitätsbibliothek Bern, https://www.bernhist.ch; Pfister und Schranz, Itinera 17 (1995), 46–78;
  Pfister, Im Strom der Modernisierung, Bern 1995.
