"""Rechenlogik und Zuordnungen der Abdeckungsmessung (scripts/85_abdeckung.py)."""

import importlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
m = importlib.import_module("85_abdeckung")


def eintrag(**kw) -> dict:
    r = dict.fromkeys(("surname", "forename", "alliance_name", "civil_status", "occupation_raw", "title", "text",
                       "building_no", "dash_prefix", "street_raw"), "")
    r.update(kw)
    return r


class Rechnen(unittest.TestCase):
    def test_interpolation(self):
        self.assertEqual(m.interpoliere(1880, 100, 1888, 180, 1883), 130)
        self.assertEqual(m.interpoliere(1900, 5, 1900, 5, 1900), 5)
        self.assertEqual(m.interpoliere(1880, 100, 1888, 180, 1888), 180)

    def test_keine_extrapolation(self):
        with self.assertRaises(ValueError):
            m.interpoliere(1880, 100, 1888, 180, 1900)

    def test_quote_und_jahresrate(self):
        self.assertEqual(m.quote(1, 8), 12.5)
        self.assertEqual(m.jahresrate(100, 200, 1), 100.0)
        self.assertEqual(m.jahresrate(100, 121, 2), 10.0)


class Nenner(unittest.TestCase):
    """Mit den eingecheckten BERNHIST-Werten."""

    @classmethod
    def setUpClass(cls):
        cls.w = m.werte_laden()

    def test_bevoelkerung(self):
        n = m.nenner(self.w, "1883")["bevoelkerung"]
        self.assertEqual(n[0], 43197 + 3 * (46009 - 43197) / 8)
        self.assertEqual(n[1], "interpoliert")
        self.assertEqual(m.nenner(self.w, "1900")["bevoelkerung"][:2], (64227, "direkt"))

    def test_haushalte_ueber_die_haushaltsgroesse_1888(self):
        n = m.nenner(self.w, "1900")["haushalte"]
        self.assertEqual(round(n[0]), round(64227 * 9931 / 46009))
        self.assertEqual(n[1], "geschätzt")

    def test_erwerbstaetige_1910_im_gebietsstand_von_1910(self):
        # Bevölkerung 1910 zählt ohne Bümpliz; die Erwerbstätigen müssen aus derselben Reihe kommen wie Frauen und
        # Männer (Gebietsstand 1910), nicht aus der Reihe mit Bümpliz (37 247).
        w = m.werte_laden()
        self.assertEqual(w["erw_1910"], w["erw_frauen_1910"] + w["erw_maenner_1910"])
        self.assertEqual(w["erw_s3_1910"], w["erw_1910"] - w["erw_s1_1910"] - w["erw_s2_1910"])

    def test_sektoren_summieren_zu_den_erwerbstaetigen(self):
        for band in ("1883", "1900"):
            n = m.nenner(self.w, band)
            self.assertAlmostEqual(sum(n[f"sektor{s}"][0] for s in "123"), n["erwerbstaetige"][0], places=6)

    def test_alle_werte_haben_ort_thema_jahr_quelle(self):
        rows = m.lies(m.WERTE)
        self.assertEqual({r["schluessel"] for r in rows}, set(m.ABFRAGE))
        for r in rows:
            self.assertEqual(r["ort_id"], "457")
            self.assertTrue(r["thema"] and r["jahr"] and r["quelle"] and r["data_entry_id"])
            self.assertEqual(int(r["jahr"]), m.ABFRAGE[r["schluessel"]][1])


class Art(unittest.TestCase):
    def test_person_trotz_firmenwort_in_der_adresse(self):
        self.assertEqual(m.art(eintrag(surname="Hirschi", forename="Joh", text="— Joh., Zimmermann, Längg., Gesellschaftstrasse 33", building_no="33")), "person")
        self.assertEqual(m.art(eintrag(surname="Schneider", forename="E", text="Schneider, E., in Fa. F. de Quervain & E. Schneider, Kramgasse 11", building_no="11")), "person")

    def test_firma(self):
        self.assertEqual(m.art(eintrag(surname="Hotz", forename="& Sohn, C", text="— & Sohn, C., Optiker", building_no="46")), "firma")
        self.assertEqual(m.art(eintrag(surname="v. Ernst", dash_prefix="1", text="— & Comp., Banquiers, Bärenpl. 4", building_no="4")), "firma")

    def test_geerbter_firmenname_ist_eine_person(self):
        self.assertEqual(m.art(eintrag(surname="Jäggi & Cie.", forename="Lina", dash_prefix="1", text="— -Reinhard, Lina, Wwe.", building_no="60")), "person")

    def test_institution_und_verweis(self):
        self.assertEqual(m.art(eintrag(surname="Staatskanzlei", text="Staatskanzlei, Postgasse.")), "institution")
        self.assertEqual(m.art(eintrag(surname="Rüdt", text="Rüdt, s. auch Rüd")), "verweis")
        self.assertEqual(m.art(eintrag(surname="Megert", occupation_raw="Dienstmann", text="Megert, Dienstmann, Schauplg. 37", building_no="37")), "person")


class Frauen(unittest.TestCase):
    def test_stand(self):
        self.assertEqual(m.frau(eintrag(civil_status="Wwe.")), "witwe")
        self.assertEqual(m.frau(eintrag(civil_status="Wittwe")), "witwe")
        self.assertEqual(m.frau(eintrag(civil_status="Frl.")), "fraeulein")
        self.assertEqual(m.frau(eintrag(civil_status="Frau")), "frau")

    def test_vorname_oder_beruf(self):
        self.assertEqual(m.frau(eintrag(forename="Rosa", occupation_raw="Glätterin")), "weiblich")
        self.assertEqual(m.frau(eintrag(forename="M", occupation_raw="Damenschneiderin")), "weiblich")
        self.assertEqual(m.frau(eintrag(forename="Joh", occupation_raw="Schreiner")), "")
        self.assertEqual(m.frau(eintrag(forename="J", occupation_raw="Schneider bei Hrn. Bloch")), "")


class Sektor(unittest.TestCase):
    def test_sektoren(self):
        for beruf, s in (("Landwirt", "1"), ("Handelsgärtner", "1"), ("Schreiner", "2"), ("Damenschneiderin", "2"),
                         ("Glätterin", "2"), ("Schriftsetzer", "2"), ("Fabrikarbeiter", "2"), ("Bäckermeister", "2"),
                         ("Postcommis", "3"), ("Wirth zur Börse", "3"), ("Lehrerin", "3"), ("Kaufmann", "3"),
                         ("Handelsmann", "3"), ("Bahnarbeiter", "3"), ("Kindergärtnerin", "3"), ("Amtsnotar", "3")):
            self.assertEqual(m.sektor(beruf), s, beruf)

    def test_handel_vor_handwerk_nur_wenn_er_zuerst_steht(self):
        self.assertEqual(m.sektor("Schuhhandlung"), "3")
        self.assertEqual(m.sektor("Schuhmacher u. Schuhhandlung"), "2")
        self.assertEqual(m.sektor("Schneider bei Hrn. Bloch"), "2")

    def test_aufzaehlung_mit_bindestrich_bleibt_ganz(self):
        self.assertEqual(m.erste_angabe("Milch-, Anken- u. Käsehändler, Aarbergg. 5"), "Milch- Anken- u. Käsehändler")
        self.assertEqual(m.sektor("Milch-, Anken- u. Käsehändler"), "3")

    def test_ohne_erwerb_und_ohne_angabe(self):
        self.assertEqual(m.sektor("Privatière"), "ohne")
        self.assertEqual(m.sektor("gew. Wirt"), "ohne")
        self.assertEqual(m.sektor("d. Schweinmetzg.", witwe=True), "ohne")
        self.assertEqual(m.sektor("Privatdocent"), "3")
        self.assertEqual(m.sektor(""), "")
        self.assertEqual(m.sektor("", "Dr. med."), "3")
        self.assertEqual(m.sektor("Taglöhner"), "unbestimmt")


class Gruppen(unittest.TestCase):
    def test_aerzte(self):
        self.assertTrue(m.gruppe("aerzte", "prakt. Arzt"))
        self.assertFalse(m.gruppe("aerzte", "Zahnarzt"))
        self.assertFalse(m.gruppe("aerzte", "Tierarzt"))
        self.assertFalse(m.gruppe("aerzte", "", "Dr. med."))
        self.assertTrue(m.gruppe("aerzte_med", "", "Dr. med."))
        self.assertFalse(m.gruppe("aerzte_med", "Assistent", "cand. med."))

    def test_lehrpersonen(self):
        self.assertTrue(m.gruppe("lehrpersonen_primar", "Lehrerin a. d. Mattenschule"))
        self.assertFalse(m.gruppe("lehrpersonen_primar", "Lehrerin"))
        self.assertTrue(m.gruppe("lehrpersonen_volksschule", "Lehrerin"))
        self.assertFalse(m.gruppe("lehrpersonen_volksschule", "Musiklehrer"))
        self.assertFalse(m.gruppe("lehrpersonen_volksschule", "Gymnasiallehrer"))
        self.assertTrue(m.gruppe("lehrpersonen_alle", "Musiklehrer"))

    def test_dienstboten_und_tagloehner(self):
        self.assertTrue(m.gruppe("dienstboten", "Hausknecht"))
        self.assertFalse(m.gruppe("dienstboten", "Kfm. in Fma. Karl Knecht & Cie."))
        self.assertFalse(m.gruppe("dienstboten", "Dienstmann"))
        self.assertTrue(m.gruppe("tagloehner", "Taglöhner b. Hrn. Schnell"))


class Ergebnis(unittest.TestCase):
    """Die eingecheckten Tabellen kommen aus dem Skript heraus."""

    @classmethod
    def setUpClass(cls):
        cls.w = m.werte_laden()
        e, b = m.lade("04_entries.csv"), m.lade("04_berufe.csv")
        cls.z = {band: m.zaehle(e, b, band) for band in ("1883", "1900")}

    def test_bandgroessen(self):
        self.assertEqual((self.z["1883"]["eintraege"], self.z["1883"]["register"]), (8241, 4226))
        self.assertEqual((self.z["1900"]["eintraege"], self.z["1900"]["register"]), (15182, 7094))
        for band in self.z:
            self.assertEqual(sum(self.z[band]["art"].values()), self.z[band]["eintraege"])
            self.assertEqual(sum(self.z[band]["sektor"].values()), self.z[band]["personen"])

    def test_abdeckung_csv(self):
        soll = [{k: str(v) for k, v in r.items()} for r in m.zeilen(self.w, self.z)]
        ist = m.lies(m.OUT_DIR / "abdeckung.csv")
        self.assertEqual(ist, soll)

    def test_wachstum_csv(self):
        soll = [{k: str(v) for k, v in r.items()} for r in m.wachstum(self.w, self.z)]
        self.assertEqual(m.lies(m.OUT_DIR / "wachstum.csv"), soll)

    def test_stichprobe(self):
        n, richtig, geaendert = m.trefferquote()
        self.assertGreaterEqual(n, 80)
        self.assertEqual(geaendert, 0, "Regeln geändert: Stichprobe neu ziehen und neu beurteilen")
        self.assertGreaterEqual(richtig / n, 0.9)


if __name__ == "__main__":
    unittest.main()
