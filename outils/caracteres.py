#!/usr/bin/env python3
"""QuizzNSI : recherche des caractères invisibles ou trompeurs dans les fichiers du dépôt.

Lancement, depuis la racine : python3 -I outils/caracteres.py [FICHIER ...]
Sans argument : tous les fichiers texte du dépôt (par leur extension, plus LICENSE, .gitignore et
.nojekyll), sauf vendor/ (bibliothèques tierces) et .git/.

Relève, avec le fichier, la ligne et la colonne :
- les caractères de contrôle (sauf tabulation et fin de ligne) ;
- les caractères invisibles : espaces et gluons sans largeur, BOM, trait d'union conditionnel,
  séparateurs de ligne Unicode, caractères privés ;
- les contrôles bidirectionnels, qui peuvent maquiller l'ordre réel d'un code ;
- les points de substitution (U+2022, U+2219, U+22C5, U+2027) entre deux lettres, là où le point
  médian U+00B7 du langage inclusif était sans doute voulu.
Les points médians et les espaces insécables sont permis. Les caractères trouvés sont affichés sous
la forme U+XXXX, jamais tels quels. Code de sortie 1 si un caractère est relevé.
Licence MIT, Babash - NSI Tani Malandi.
"""
import os
import sys
import unicodedata

EXTENSIONS = {".html", ".css", ".js", ".json", ".md", ".py", ".yml", ".yaml", ".txt", ".svg"}
SANS_EXTENSION = {"LICENSE", ".gitignore", ".nojekyll"}  # fichiers texte sans extension, lus aussi
IGNORES = {".git", "vendor", "__pycache__", "captures"}
POINTS = {0x2022, 0x2219, 0x22C5, 0x2027}
PERMIS = {0x00A0, 0x202F, 0x00B7}


def a_relever(c, avant, apres):
    o = ord(c)
    if c in "\n\r\t" or o in PERMIS:
        return None
    cat = unicodedata.category(c)
    if cat == "Cc":
        return "contrôle"
    if cat == "Cf":
        return "bidirectionnel" if 0x202A <= o <= 0x202E or 0x2066 <= o <= 0x2069 or o in (0x200E, 0x200F, 0x061C) else "invisible"
    if cat in ("Co", "Cs", "Cn"):
        return "privé ou non attribué"
    if cat in ("Zl", "Zp") or (cat == "Zs" and c != " "):
        return "espace ou séparateur particulier"
    if o in (0x3164, 0x115F, 0x1160, 0xFFA0, 0x2800):
        return "lettre de remplissage invisible"
    if o in POINTS and avant.isalpha() and apres.isalpha():
        return "point de substitution (point médian U+00B7 attendu ?)"
    return None


def fichiers(racine):
    for d, sous, noms in os.walk(racine):
        sous[:] = sorted(s for s in sous if s not in IGNORES)
        for n in sorted(noms):
            if os.path.splitext(n)[1] in EXTENSIONS or n in SANS_EXTENSION:
                yield os.path.join(d, n)


def main(args):
    racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    liste = args or list(fichiers(racine))
    trouves = 0
    for chemin in liste:
        try:
            texte = open(chemin, encoding="utf-8").read()
        except UnicodeDecodeError:
            print(f"{os.path.relpath(chemin, racine)} : n'est pas en UTF-8")
            trouves += 1
            continue
        for n, ligne in enumerate(texte.split("\n"), 1):
            for i, c in enumerate(ligne):
                quoi = a_relever(c, ligne[i - 1] if i else "", ligne[i + 1] if i + 1 < len(ligne) else "")
                if quoi:
                    trouves += 1
                    print(f"{os.path.relpath(chemin, racine)}:{n}:{i + 1} : U+{ord(c):04X} ({quoi})")
    print(f"{len(liste)} fichiers lus, {trouves} caractère(s) à relire")
    return 1 if trouves else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
