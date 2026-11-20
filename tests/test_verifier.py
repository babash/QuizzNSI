"""QuizzNSI : tests du vérificateur de cours.

Lancement, depuis la racine de QuizzNSI : python3 -I -m unittest discover -s tests -p "test_*.py"
"""
import copy
import json
import os
import sys
import tempfile
import unittest

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RACINE, "outils"))
import verifier_cours as V  # noqa: E402

with open(os.path.join(RACINE, "cours", "piles-files.json"), encoding="utf-8") as f:
    MODELE = json.load(f)


with open(os.path.join(RACINE, "cours", "revision-conditions-boucles.json"), encoding="utf-8") as f:
    REVISION = json.load(f)


def autre(c, t):
    return next(d for d in c["diapositives"] if d["type"] == t)


def questions(c):
    return [d for d in c["diapositives"] if d["type"] == "question"]


class TestVerifier(unittest.TestCase):
    def verifier(self, cours, executer=False):
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, cours["id"] + ".json")
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(cours, f, ensure_ascii=False)
            r, _ = V.verifier_cours(chemin, executer_code=executer)
        return r.erreurs

    def modifie(self, f):
        c = copy.deepcopy(MODELE)
        f(c)
        return self.verifier(c)

    def test_le_cours_livre_est_conforme_avec_execution(self):
        self.assertEqual(self.verifier(copy.deepcopy(MODELE), executer=True), [])

    # ── les autres types de questions ──
    def rev(self, f, executer=False):
        c = copy.deepcopy(REVISION)
        f(c)
        return self.verifier(c, executer)

    def test_revision_avec_les_autres_types_conforme_avec_execution(self):
        self.assertEqual(self.verifier(copy.deepcopy(REVISION), executer=True), [])

    def test_le_melange_est_celui_du_navigateur(self):
        # les mêmes valeurs que js/commun.js (tests/test_moteur.js) : la page et le vérificateur voient le même ordre
        self.assertEqual(V.graine("a02"), 3771486418)
        self.assertEqual(V.melanger(range(10), V.graine("a02")), [8, 5, 1, 3, 4, 7, 0, 6, 9, 2])

    def test_relier_une_seule_paire(self):
        e = self.rev(lambda c: autre(c, "relier").update(paires=autre(c, "relier")["paires"][:1]))
        self.assertTrue(any("paires" in x for x in e))

    def test_relier_deux_reponses_identiques(self):
        e = self.rev(lambda c: autre(c, "relier")["paires"][1].update(droite=autre(c, "relier")["paires"][0]["droite"]))
        self.assertTrue(any("identiques" in x for x in e))

    def test_relier_verification_fausse(self):
        e = self.rev(lambda c: autre(c, "relier")["paires"][0]["verification"].update(sortie="16"), executer=True)
        self.assertTrue(any("sortie attendue" in x for x in e))

    def test_puzzle_solution_executee(self):
        e = self.rev(lambda c: autre(c, "puzzle")["verifications"][0].update(sortie="25"), executer=True)
        self.assertTrue(any("sortie attendue '25'" in x for x in e))

    def test_puzzle_indentation_irreguliere(self):
        e = self.rev(lambda c: autre(c, "puzzle")["lignes"].__setitem__(2, "  if i % 2 == 0:"))
        self.assertTrue(any("indentation" in x for x in e))

    def test_puzzle_sans_verification(self):
        e = self.rev(lambda c: autre(c, "puzzle").pop("verifications"))
        self.assertTrue(any("vérification" in x for x in e))

    def test_ligne_fautive_hors_du_code(self):
        e = self.rev(lambda c: autre(c, "ligne").update(ligne=99))
        self.assertTrue(any("numéro" in x for x in e))

    def test_ligne_correction_qui_ne_corrige_pas(self):
        e = self.rev(lambda c: autre(c, "ligne").update(correction="    for i in range(1, n + 2):"), executer=True)
        self.assertTrue(any("code corrigé" in x for x in e))

    def test_ligne_piege_sur_la_bonne_ligne(self):
        e = self.rev(lambda c: autre(c, "ligne")["pieges"].update({"3": "Ce feedback vise la bonne ligne, ce n'est pas un piège du tout."}))
        self.assertTrue(any("pieges" in x for x in e))

    def test_autre_type_champ_inconnu(self):
        e = self.rev(lambda c: autre(c, "nuage").update(html="<b>x</b>"))
        self.assertTrue(any("champ inconnu" in x for x in e))

    def test_toujours_20_questions_a_choix(self):
        e = self.rev(lambda c: c["diapositives"].remove(questions(c)[0]))
        self.assertTrue(any("19 questions" in x for x in e))

    def test_trois_options(self):
        e = self.modifie(lambda c: questions(c)[0]["options"].pop())
        self.assertTrue(any("4 options" in x for x in e))

    def test_deux_reponses_justes(self):
        e = self.modifie(lambda c: questions(c)[0]["options"][0].update(juste=True))
        self.assertTrue(any("une seule option juste" in x for x in e))

    def test_feedback_vide(self):
        e = self.modifie(lambda c: questions(c)[2]["options"][1].update(feedback="Non."))
        self.assertTrue(any("feedback" in x for x in e))

    def test_objectif_manquant(self):
        e = self.modifie(lambda c: questions(c)[3].pop("objectif"))
        self.assertTrue(any("objectif" in x for x in e))

    def test_gras_dans_une_option(self):
        e = self.modifie(lambda c: questions(c)[0]["options"][1].update(texte="Une **pile**"))
        self.assertTrue(any("gras" in x for x in e))

    def test_caractere_invisible(self):
        e = self.modifie(lambda c: questions(c)[0].update(nom="Pile" + chr(0x200B)))
        self.assertTrue(any("U+200B" in x for x in e))

    def test_nombre_de_questions(self):
        def retirer(c):
            q = questions(c)[-1]
            c["diapositives"].remove(q)
        e = self.modifie(retirer)
        self.assertTrue(any("19 questions" in x for x in e))

    def test_repartition_desequilibree(self):
        def tout_en_a(c):
            for q in questions(c):
                j = next(o for o in q["options"] if o.get("juste"))
                q["options"].remove(j)
                q["options"].insert(0, j)
        e = self.modifie(tout_en_a)
        self.assertTrue(any("répartition" in x for x in e))

    def test_sortie_fausse_detectee_a_l_execution(self):
        c = copy.deepcopy(MODELE)
        questions(c)[4]["verifications"][0]["sortie"] = "[4, 1, 3]"
        e = self.verifier(c, executer=True)
        self.assertTrue(any("sortie attendue" in x for x in e))

    def test_erreur_attendue_detectee(self):
        c = copy.deepcopy(MODELE)
        questions(c)[7]["verifications"][0]["erreur"] = "KeyError"
        e = self.verifier(c, executer=True)
        self.assertTrue(any("erreur attendue" in x for x in e))

    def test_code_sans_verification(self):
        e = self.modifie(lambda c: next(q for q in questions(c) if q.get("code")).pop("verifications"))
        self.assertTrue(any("vérification" in x for x in e))

    def test_svg_avec_script_refuse(self):
        e = self.modifie(lambda c: questions(c)[0].update(schema={"type": "svg", "code": '<svg onload="x()"></svg>'}))
        self.assertTrue(any("svg" in x for x in e))


    def schema(self, c, test):
        return next(d["schema"] for d in c["diapositives"] if isinstance(d.get("schema"), dict) and test(d["schema"]))

    def test_schema_deux_piles_faux(self):
        # l'erreur relevée par le Gardien : la pile auxiliaire dessinée dans le même ordre que p
        c = copy.deepcopy(MODELE)
        self.schema(c, lambda s: s["type"] == "deux-piles" and s["droite"]["nom"] == "aux")["droite"]["elements"] = ["c", "b", "a"]
        self.assertTrue(any("schéma faux" in x and "aux" in x for x in self.verifier(c, executer=True)))

    def test_schema_etapes_etat_faux(self):
        c = copy.deepcopy(MODELE)
        self.schema(c, lambda s: s.get("variable") == "f")["etapes"][3]["elements"] = ["a", "b"]
        self.assertTrue(any("schéma faux" in x for x in self.verifier(c, executer=True)))

    def test_schema_etapes_valeur_renvoyee_fausse(self):
        c = copy.deepcopy(MODELE)
        s = self.schema(c, lambda s: s.get("variable") == "p" and s["etapes"][0]["op"] == "p = Pile()")
        s["etapes"][3]["op"] = "p.depiler() → 4"
        self.assertTrue(any("renvoie 1" in x for x in self.verifier(c, executer=True)))


    def test_nom_de_variable_inconnu_dans_une_option(self):
        def f(c):
            q = next(q for q in questions(c) if q.get("code") and any("impressions" in l for l in q["code"]))
            q["options"][1]["texte"] = "Il faut écrire `file.pop(0)`."
        self.assertTrue(any("« file »" in x for x in self.modifie(f)))

    def test_renvoi_a_une_question_suivante(self):
        def f(c):
            q = questions(c)[3]
            q["enonce"][0] += " Comme à la question 4."
        self.assertTrue(any("renvoi à la question 4" in x for x in self.modifie(f)))


class TestCatalogue(unittest.TestCase):
    """Le contrôle du catalogue de l'accueil (verifier_cours.py --tous)."""
    def essai(self, ids):
        import contextlib, io, shutil
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "outils")); os.makedirs(os.path.join(d, "cours"))
            shutil.copy(os.path.join(RACINE, "outils", "verifier_cours.py"), os.path.join(d, "outils"))
            shutil.copy(os.path.join(RACINE, "cours", "piles-files.json"), os.path.join(d, "cours"))
            with open(os.path.join(d, "cours", "catalogue.json"), "w", encoding="utf-8") as f:
                json.dump({"format": "quizz-nsi-catalogue/1", "cours": [{"id": i, "titre": i, "niveau": "x", "questions": 20} for i in ids]}, f)
            sys.path.insert(0, os.path.join(d, "outils"))
            import importlib, verifier_cours as W
            importlib.reload(W)
            sys.path.pop(0)
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                code = W.main(["--tous", "--sans-execution"])
            return code, sortie.getvalue()

    def test_catalogue_conforme(self):
        self.assertEqual(self.essai(["piles-files"])[0], 0)

    def test_cours_cite_mais_absent(self):
        self.assertEqual(self.essai(["piles-files", "arbres"])[0], 1)

    def test_cours_present_non_cite(self):
        self.assertEqual(self.essai([])[0], 1)

    def test_doublon(self):
        self.assertEqual(self.essai(["piles-files", "piles-files"])[0], 1)


class TestCaracteres(unittest.TestCase):
    def test_caracteres_releves(self):
        sys.path.insert(0, os.path.join(RACINE, "outils"))
        import caracteres as C
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "x.md")
            with open(f, "w", encoding="utf-8") as h:
                h.write("a" + chr(0x200B) + "b " + chr(0x202E) + " élève" + chr(0x2022) + "s enseignant·e" + chr(0xA0) + "!")
            self.assertEqual(C.main([f]), 1)
            with open(f, "w", encoding="utf-8") as h:
                h.write("enseignant·e" + chr(0xA0) + "!")
            self.assertEqual(C.main([f]), 0)


if __name__ == "__main__":
    unittest.main()
