#!/usr/bin/env python3
"""QuizzNSI : parcours complets dans un vrai navigateur (Playwright, Chromium).

Lancement, depuis la racine de QuizzNSI :
    python3 -I tests/test_parcours.py [DOSSIER_DES_CAPTURES]

1. Une séance en classe avec un·e enseignant·e et deux élèves (Kobalt et Ixo, à 320 px),
   par le chemin « en ligne » de js/seance.js, mais avec un faux client temps réel
   (tests/faux-temps-reel.js) : aucune requête ne sort, la base n'est jamais appelée.
   On contrôle : le pseudo invisible refusé, le pseudo déjà pris refusé, le pseudo retiré par
   l'enseignant·e, les 20 questions, les points de chaque élève (recalculés ici d'après le barème),
   le podium et l'écran de fin.
1 bis. Injection : un·e élève malveillant·e qui connaît le code de séance envoie, pour chaque type de
   message et chaque champ, une valeur forgée (balise <img onerror>, nombre énorme, négatif, objet,
   chaîne très longue). Un piège sur innerHTML, outerHTML, insertAdjacentHTML, createContextualFragment
   et document.write échoue si une donnée venue du canal (marquée XSSMARK) y passe, même échappée :
   les deux élèves ont un pseudo qui contient XSSMARK, le podium est affiché après chaque question.
1 quater. Les autres types de questions en séance (nuage de mots, relier, puzzle de code, ligne fautive) :
   deux téléphones et la page projetée ; le mot du nuage filtré, caché puis montré, masqué ; les points
   (en proportion pour relier) ; un piège à innerHTML et un espion sur le canal.
1 ter. Le QR code en très grand (bouton et touche Q), à l'accueil et pendant une question, à 3 largeurs et
   dans les 2 thèmes ; un·e élève en retard rejoint en pleine question et reçoit ses points.
2. Le mode autonome : les diapositives, une erreur puis la bonne réponse, le bilan ;
   rejouer le quiz : les 20 questions dans un autre ordre, les réponses mélangées, rien d'envoyé.
3. La version imprimable : le sujet et le corrigé en PDF A4, sans débordement.
4. Toutes les pages à 320, 768 et 1440 px, en clair et en obscur : aucun défilement horizontal.
Aucune erreur JavaScript n'est tolérée ; toute requête vers un autre site est bloquée et signalée.
"""
import functools
import http.server
import json
import os
import sys
import threading

from playwright.sync_api import sync_playwright

RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SORTIE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(RACINE, "tests", "captures")
os.makedirs(SORTIE, exist_ok=True)
with open(os.path.join(RACINE, "cours", "piles-files.json"), encoding="utf-8") as f:
    COURS = json.load(f)
QUESTIONS = [d for d in COURS["diapositives"] if d["type"] == "question"]
BONNES = [next(i for i, o in enumerate(q["options"]) if o.get("juste")) for q in QUESTIONS]
with open(os.path.join(RACINE, "tests", "faux-temps-reel.js"), encoding="utf-8") as f:
    FAUX = f.read()

erreurs, externes = [], []


def serveur():
    class Silencieux(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    gestion = functools.partial(Silencieux, directory=RACINE)
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestion)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_address[1]}/"


def surveiller(page, nom):
    page.on("pageerror", lambda e: erreurs.append(f"{nom} : {e}"))
    page.on("console", lambda m: erreurs.append(f"{nom} (console) : {m.text}") if m.type == "error" else None)


def contexte(navigateur, base, **kw):
    ctx = navigateur.new_context(**kw)

    def route(r):
        url = r.request.url
        if url.endswith("/vendor/temps-reel.js"):
            return r.fulfill(status=200, content_type="text/javascript", body=FAUX)
        if not url.startswith(base) and not url.startswith("data:") and not url.startswith("blob:"):
            externes.append(url)
            return r.abort()
        return r.continue_()
    ctx.route("**/*", route)
    return ctx


MARQUE = "XSSMARK"
BALISE = '<img src=x onerror="window.__pwned=1">' + MARQUE
PIEGE = """
(() => {
  window.__piege = [];
  const M = 'XSSMARK', note = (ou, v) => { if (String(v).includes(M)) window.__piege.push(ou + ' : ' + String(v).slice(0, 80)); };
  for (const p of ['innerHTML', 'outerHTML']) {
    const d = Object.getOwnPropertyDescriptor(Element.prototype, p);
    Object.defineProperty(Element.prototype, p, { configurable: true, get() { return d.get.call(this); }, set(v) { note(p, v); d.set.call(this, v); } });
  }
  const iah = Element.prototype.insertAdjacentHTML;
  Element.prototype.insertAdjacentHTML = function (w, v) { note('insertAdjacentHTML', v); return iah.call(this, w, v); };
  const ccf = Range.prototype.createContextualFragment;
  Range.prototype.createContextualFragment = function (v) { note('createContextualFragment', v); return ccf.call(this, v); };
  const dw = Document.prototype.write;
  Document.prototype.write = function (...v) { note('document.write', v.join('')); return dw.apply(this, v); };
})();
"""


def forges(moi, autre):
    """Pour chaque type de message et chaque champ (imbriqué compris), des copies avec une valeur forgée."""
    import copy
    cle = {"x": "A" * 43, "y": "B" * 43}
    modeles = [
        {"t": "attente"},
        {"t": "notion", "cours": "piles-files", "n": 1, "f": 0},
        {"t": "question", "cours": "piles-files", "qid": "q01", "reste": 1000, "duree": 45, "ferme": False},
        {"t": "fermee", "qid": "q01"},
        {"t": "recus", "qid": "q01", "n": ["00112233aabbccdd"]},
        {"t": "retire", "id": moi},
        {"t": "refus", "id": moi, "raison": "pris"},
        {"t": "correction", "cours": "piles-files", "qid": "q01", "precedente": None, "bonne": 1, "rep": [1, 1, 0, 0],
         "bareme": {"participation": 10, "juste": 100, "rapidite": 20, "rebond": 30}, "duree": 0,
         "podium": [{"pseudo": "Kobalt", "total": 110, "place": 1}]},
        {"t": "fin", "cours": "piles-files", "podium": [{"pseudo": "Kobalt", "total": 110, "place": 1}]},
        {"t": "corrige", "cours": "piles-files", "qid": "q01", "precedente": None, "duree": 0, "nb": 2, "justes": 1,
         "podium": [{"pseudo": "Kobalt", "total": 110, "place": 1}]},
        {"t": "bonjour", "id": autre},
        {"t": "rep", "de": cle, "iv": "abcdefghijklmnop", "donnees": "QUJDRA"},
    ]
    valeurs = [BALISE, 10 ** 300, -1, 2.5, {"html": BALISE}, [BALISE], BALISE * 2000, True]

    def feuilles(o, base=()):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from feuilles(v, base + (k,))
        elif isinstance(o, list) and o:
            for i, v in enumerate(o):
                yield from feuilles(v, base + (i,))
        else:
            yield base
    for m in modeles:
        for ch in feuilles(m):
            if ch == ("t",):
                continue
            for v in valeurs:
                c = copy.deepcopy(m)
                x = c
                for k in ch[:-1]:
                    x = x[k]
                if isinstance(x[ch[-1]], bool) and isinstance(v, bool):
                    continue
                x[ch[-1]] = v
                yield c
        c = copy.deepcopy(m)
        c["html"] = BALISE
        yield c


def injection(nav, base):
    ctx = contexte(nav, base)
    ctx.add_init_script(PIEGE)
    prof = ctx.new_page()
    prof.set_viewport_size({"width": 1440, "height": 900})
    surveiller(prof, "injection enseignant·e")
    prof.goto(base + "animer.html?cours=piles-files")
    attendre_texte(prof, "#etatConnexion", "Séance ouverte")
    code = prof.inner_text("#code").strip()
    eleves = []
    for pseudo in ("Kobalt " + MARQUE, MARQUE):
        e = ctx.new_page()
        e.set_viewport_size({"width": 320, "height": 740})
        surveiller(e, "injection " + pseudo)
        e.goto(base + f"rejoindre.html?s={code}")
        e.fill("#champPseudo", pseudo)
        e.click("#rejoindre")
        eleves.append(e)
    attendre_texte(prof, "#eleves", "Kobalt " + MARQUE)
    prof.select_option("#duree", "0")
    prof.select_option("#podium", "chaque")
    prof.click("#commencer")
    premiere = next(i for i, d in enumerate(COURS["diapositives"]) if d["type"] == "question")
    suivante(prof, "#action", "#compteur", premiere)  # jusqu'à la question 1
    for e in eleves:
        e.wait_for_selector('button.option[data-choix="1"]:not([disabled])')
    moi = eleves[0].evaluate("() => JSON.parse(sessionStorage.getItem('quizz-nsi:eleve')).id")
    autre = eleves[1].evaluate("() => JSON.parse(sessionStorage.getItem('quizz-nsi:eleve')).id")
    attaque = ctx.new_page()
    attaque.goto(base + "index.html")
    liste = list(forges(moi, autre))
    attaque.evaluate("""([canal, msgs, balise, moi]) => {
        const bc = new BroadcastChannel('faux:' + canal);
        for (const m of msgs) bc.postMessage({ k: 'b', event: 'm', payload: m });
        // une présence forgée : pseudo piégé, identifiant piégé, clé en plus
        bc.postMessage({ k: 'p', cle: 'x1', info: { id: 'aaaaaaaaaaaaaaaa', pseudo: balise, role: 'eleve' } });
        bc.postMessage({ k: 'p', cle: 'x2', info: { id: balise, pseudo: 'Ixo', role: 'eleve' } });
        bc.postMessage({ k: 'p', cle: 'x3', info: { id: 'bbbbbbbbbbbbbbbb', pseudo: 'Ixo', role: 'eleve', html: balise } });
        bc.postMessage({ k: 'p', cle: 'x4', info: { id: 'cccccccccccccccc', pseudo: 'x'.repeat(100000), role: 'eleve' } });
        bc.postMessage({ k: 'p', cle: 'x5', info: { id: 'dddddddddddddddd', role: 'hote' } });
    }""", ["quizz-nsi:" + code, liste, BALISE, moi])
    prof.wait_for_timeout(1500)
    attendre_texte(prof, "#autreHote", "une autre page projetée")  # la présence forgée d'une page projetée
    # un espion écoute tout le canal pendant la suite de la séance
    espion = ctx.new_page()
    espion.goto(base + "index.html")
    espion.evaluate("canal => { window.__vus = []; const bc = new BroadcastChannel('faux:' + canal); bc.onmessage = ({ data }) => { if (data.k === 'b') window.__vus.push(data.payload); }; }", "quizz-nsi:" + code)
    # la séance continue normalement après l'attaque
    eleves[0].click('button.option[data-choix="1"]')
    eleves[1].click('button.option[data-choix="0"]')
    attendre_texte(prof, "#statutQ", "Tout le monde a répondu")
    prof.click("#action")
    prof.wait_for_selector("#podiumBoite[open]")
    attendre_texte(prof, "#podiumCorps", "Kobalt " + MARQUE)
    attendre_texte(eleves[0], ".q-num", "Question 1 sur 20 · correction")
    attendre_texte(eleves[0], "#points", "110 pts")
    fermer = "() => { const b = document.getElementById('podiumBoite'); if (b.open) b.close(); }"
    for _ in range(250):  # jusqu'à la fin, en fermant le podium affiché après chaque question
        prof.wait_for_timeout(120)
        if prof.inner_text("#action").startswith("Revoir"):
            break
        prof.evaluate(fermer)
        prof.click("#action")
    prof.wait_for_selector("#podiumBoite[open]")
    attendre_texte(eleves[1], "#ecran", "Fin de la séance")
    for nom, p in (("enseignant·e", prof), ("élève 1", eleves[0]), ("élève 2", eleves[1])):
        piege = p.evaluate("window.__piege")
        assert not piege, f"{nom} : une donnée du canal est passée par du HTML : {piege[:3]}"
        assert p.evaluate("window.__pwned") is None, f"{nom} : script exécuté"
        assert p.evaluate("document.querySelectorAll('img').length") == 0, f"{nom} : une image a été créée"
        assert "aaaaaaaaaaaaaaaa" not in p.content() and "<img" not in p.inner_html("body"), f"{nom} : élément forgé affiché"
    assert "Ixo" not in prof.inner_text("#eleves"), "présence forgée affichée"
    # ce que l'espion a vu : aucune réponse lisible, aucun résultat individuel
    vus = espion.evaluate("window.__vus")
    reps = [m for m in vus if m.get("t") == "rep"]
    assert len(reps) >= 2, "les réponses des deux élèves auraient dû passer (chiffrées)"
    for m in vus:
        texte = json.dumps(m)
        if m.get("t") in ("rep", "correction", "fin", "recus", "question"):
            assert moi not in texte and autre not in texte, f"identifiant d'élève diffusé : {texte[:120]}"
        if m.get("t") == "rep":
            assert set(m) == {"t", "de", "iv", "donnees"}, f"réponse en clair : {texte[:120]}"
        if m.get("t") in ("correction", "fin"):
            assert "res" not in m, "résultats individuels diffusés"
    print(f"  confidentialité : {len(vus)} messages écoutés, {len(reps)} réponses chiffrées, aucun résultat individuel")
    print(f"  injection : {len(liste)} messages forgés et 5 présences forgées ignorés (la fausse page projetée est signalée) ; aucun innerHTML ne reçoit de donnée du canal")
    ctx.close()


def suivante(page, bouton, compteur, i):
    """Clique « Suite » ou « Suivante » jusqu'à la diapositive i (les apparitions progressives passent d'abord)."""
    for _ in range(30):
        if page.inner_text(compteur).startswith(f"{i + 1} /") or page.inner_text(compteur).startswith(f"Diapositive {i + 1} sur"):
            return
        page.click(bouton)
        page.wait_for_timeout(40)
    raise AssertionError(f"diapositive {i + 1} jamais atteinte")


def points(juste, precedente):
    """Le barème de js/bareme.js, sans minuterie : +10 pour répondre, +100 si juste, +30 de rebond."""
    return 10 + (100 if juste else 0) + (30 if juste and precedente == "faux" else 0)


def attendre_texte(page, selecteur, texte, delai=8000):
    page.wait_for_function("([s, t]) => { const e = document.querySelector(s); return e && e.innerText.includes(t); }", arg=[selecteur, texte], timeout=delai)


def seance(nav, base):
    ctx = contexte(nav, base)
    prof = ctx.new_page()
    prof.set_viewport_size({"width": 1440, "height": 900})
    surveiller(prof, "enseignant·e")
    prof.goto(base + "animer.html?cours=piles-files")
    attendre_texte(prof, "#etatConnexion", "Séance ouverte")
    code = prof.inner_text("#code").strip()
    assert len(code) == 4, code
    journal = prof.evaluate("window.__fauxTempsReel")
    assert journal["clients"][0]["url"] == "wss://cukahpyqkljiddmimpyi.supabase.co/realtime/v1", journal
    assert journal["clients"][0]["apikey"].startswith("sb_publishable_"), "clé publishable attendue"

    def eleve(pseudo, largeur=320, theme="light"):
        p = ctx.new_page()
        p.set_viewport_size({"width": largeur, "height": 740})
        p.emulate_media(color_scheme=theme)
        surveiller(p, pseudo)
        p.goto(base + f"rejoindre.html?s={code}")
        p.fill("#champPseudo", pseudo)
        p.click("#rejoindre")
        return p

    # un pseudo avec un caractère invisible est refusé avant tout envoi
    p0 = ctx.new_page(); surveiller(p0, "invisible")
    p0.goto(base + f"rejoindre.html?s={code}")
    p0.fill("#champPseudo", "Ko" + chr(0x200B) + "balt")
    p0.click("#rejoindre")
    assert "invisible" in p0.inner_text("#erreurPseudo"), p0.inner_text("#erreurPseudo")
    p0.close()

    eleve_1 = eleve("Kobalt", theme="light")
    eleve_2 = eleve("Ixo", theme="dark")
    intrus = eleve("Pseudo Bizarre")
    attendre_texte(prof, "#eleves", "Pseudo Bizarre")
    attendre_texte(prof, "#eleves", "Kobalt")
    attendre_texte(prof, "#eleves", "Ixo")
    prof.screenshot(path=os.path.join(SORTIE, "seance-accueil-1440.png"))
    # le même pseudo (à la casse et aux accents près) est refusé
    double = eleve("KOBALT")
    attendre_texte(double, "#erreurPseudo", "déjà pris")
    double.close()
    # l'enseignant·e retire un pseudo : l'élève doit en choisir un autre
    prof.click('#eleves li:has-text("Pseudo Bizarre") button.retirer')
    attendre_texte(intrus, "#erreurPseudo", "retiré")
    prof.wait_for_function("() => !document.querySelector('#eleves').innerText.includes('Pseudo Bizarre')")
    intrus.fill("#champPseudo", "Pseudo Bizarre")
    intrus.click("#rejoindre")
    attendre_texte(intrus, "#erreurPseudo", "retiré")  # le pseudo retiré reste refusé
    intrus.close()

    prof.select_option("#duree", "0")
    prof.click("#commencer")
    # Kobalt : une erreur sur 4, Ixo : toujours A (ses rebonds sont rares)
    choix_n = [BONNES[k] if k % 4 != 1 else (BONNES[k] + 1) % 4 for k in range(20)]
    choix_a = [0] * 20
    attendu = {"Kobalt": 0, "Ixo": 0}
    prec = {"Kobalt": None, "Ixo": None}
    k = 0
    for i, d in enumerate(COURS["diapositives"]):
        if i > 0:
            suivante(prof, "#action", "#compteur", i)
        if d["type"] == "humour":
            # le téléphone suit les apparitions progressives de l'écran projeté
            assert eleve_1.evaluate("document.querySelectorAll('#ecran .frag.vu').length") == 0
            prof.click("#action"); prof.click("#action")
            eleve_1.wait_for_function("() => document.querySelectorAll('#ecran .frag.vu').length === 2")
            while prof.inner_text("#action").startswith("Suite"):
                prof.click("#action")
            prof.screenshot(path=os.path.join(SORTIE, "seance-humour-1440.png"))
            attendre_texte(eleve_1, "#ecran", d["chute"].rstrip("!").strip())
            eleve_1.screenshot(path=os.path.join(SORTIE, "eleve-humour-320.png"), full_page=True)
        if d["type"] != "question":
            continue
        for page, nom, ch in ((eleve_1, "Kobalt", choix_n), (eleve_2, "Ixo", choix_a)):
            page.wait_for_selector(f'section.d-question button.option[data-choix="{ch[k]}"]:not([disabled])', timeout=8000)
            attendre_texte(page, ".q-num", f"Question {k + 1} sur 20")
            if k == 2 and nom == "Kobalt":
                page.screenshot(path=os.path.join(SORTIE, "eleve-question-320.png"), full_page=True)
            page.click(f'button.option[data-choix="{ch[k]}"]')
            juste = ch[k] == BONNES[k]
            attendu[nom] += points(juste, prec[nom])
            prec[nom] = "juste" if juste else "faux"
        attendre_texte(prof, "#statutQ", "Tout le monde a répondu")
        attendre_texte(eleve_1, "#envoyee", "reçue")
        if k == 5:
            # réouverture en cours de séance : onglet fermé, QR code scanné de nouveau, sur le même appareil
            ident = eleve_1.evaluate("() => JSON.parse(sessionStorage.getItem('quizz-nsi:eleve'))")
            eleve_1.close()
            eleve_1 = ctx.new_page()
            eleve_1.set_viewport_size({"width": 320, "height": 740})
            surveiller(eleve_1, "Kobalt rouvert")
            eleve_1.goto(base + "index.html")
            # dans ce test, les deux élèves partagent le stockage du navigateur : on remet celui de Kobalt
            eleve_1.evaluate("e => localStorage.setItem('quizz-nsi:eleve', JSON.stringify(Object.assign(e, { jusqua: Date.now() + 3600000 })))", ident)
            eleve_1.goto(base + f"rejoindre.html?s={code}")
            assert eleve_1.input_value("#champPseudo") == "Kobalt"
            eleve_1.click("#rejoindre")
            attendre_texte(eleve_1, "#points", f"{attendu['Kobalt'] - points(choix_n[k] == BONNES[k], 'juste' if choix_n[k - 1] == BONNES[k - 1] else 'faux')} pts")
            eleve_1.wait_for_selector(f'button.option.choisie[data-choix="{choix_n[k]}"]')  # sa réponse est retrouvée
            print("  réouverture : points et réponse retrouvés après la fermeture de l'onglet")
        if k == 4:
            prof.screenshot(path=os.path.join(SORTIE, "seance-question-1440.png"))
        prof.click("#action")  # montrer la réponse
        for page, nom in ((eleve_1, "Kobalt"), (eleve_2, "Ixo")):
            attendre_texte(page, ".q-num", f"Question {k + 1} sur 20 · correction")
            attendre_texte(page, "#points", f"{attendu[nom]} pts")
        if k == 4:
            prof.screenshot(path=os.path.join(SORTIE, "seance-correction-1440.png"), full_page=True)
            eleve_1.screenshot(path=os.path.join(SORTIE, "eleve-correction-320.png"), full_page=True)
            eleve_2.screenshot(path=os.path.join(SORTIE, "eleve-correction-320-obscur.png"), full_page=True)
        k += 1
    assert k == 20
    prof.click("#action")  # terminer la séance
    prof.wait_for_selector("#podiumBoite[open]")
    attendre_texte(prof, "#podiumCorps", "Kobalt")
    prof.screenshot(path=os.path.join(SORTIE, "seance-podium-1440.png"))
    attendre_texte(eleve_1, "#ecran", "Fin de la séance")
    attendre_texte(eleve_1, "#ecran", f"{attendu['Kobalt']} points")
    attendre_texte(eleve_1, "#ecran", "1re place")
    eleve_1.screenshot(path=os.path.join(SORTIE, "eleve-fin-320.png"), full_page=True)
    # rejouer : le lien sur le téléphone, le QR code « rejouer » sur la page projetée (dans le podium et en grand)
    assert eleve_1.get_attribute('#ecran a.bouton.fort', "href") == "revision.html?cours=piles-files&rejouer"
    assert prof.is_visible("#rejouerBloc") and prof.locator("#qrRejouer svg").count() == 1
    assert prof.inner_text("#lienRejouer").endswith("revision.html?cours=piles-files&rejouer")
    prof.click("#btnRejouerGrand")
    prof.wait_for_selector("#qrBoite[open]")
    attendre_texte(prof, "#qrTitre", "Rejouer le quiz")
    assert not prof.is_visible("#codeGrand")
    prof.screenshot(path=os.path.join(SORTIE, "seance-rejouer-grand-1440.png"))
    prof.keyboard.press("q")
    prof.wait_for_selector("#qrBoite:not([open])", state="attached")
    assert eleve_1.evaluate("localStorage.getItem('quizz-nsi:eleve')") is None, "l'entrée « eleve » doit être effacée à la fin de la séance"
    attendre_texte(eleve_2, "#ecran", f"{attendu['Ixo']} points")
    print(f"  séance : 20 questions, points Kobalt {attendu['Kobalt']}, Ixo {attendu['Ixo']}, envois {prof.evaluate('window.__fauxTempsReel.envois')}")
    ctx.close()


def qr_et_retard(nav, base):
    """Le QR code en très grand, à tout moment (bouton ou touche Q), et un·e élève en retard qui rejoint en pleine question."""
    ctx = contexte(nav, base)
    prof = ctx.new_page()
    surveiller(prof, "QR en grand")
    for largeur, hauteur in ((1440, 900), (768, 1024), (320, 640)):
        prof.set_viewport_size({"width": largeur, "height": hauteur})
        prof.goto(base + "animer.html?cours=piles-files")
        attendre_texte(prof, "#etatConnexion", "Séance ouverte")
        prof.click("#btnQrGrand")  # dès l'accueil
        prof.wait_for_selector("#qrBoite[open]")
        taille = prof.evaluate("() => { const r = document.querySelector('#qrGrand').getBoundingClientRect(); return Math.min(r.width, r.height) / Math.min(innerWidth, innerHeight); }")
        assert taille > 0.5, f"QR code trop petit à {largeur} px : {taille:.2f} de l'écran"
        large = prof.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
        assert large <= 0, f"QR en grand à {largeur} px : défilement horizontal"
        hors = prof.evaluate("""() => [...document.querySelectorAll('#qrBoite *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.left < -1 || r.right > innerWidth + 1 || e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX === 'visible' && e.tagName !== 'svg'); }).map(e => e.id || e.className)""")
        assert not hors, f"QR en grand à {largeur} px : {hors} sort de l'écran"
        haut = prof.evaluate("() => { const b = document.querySelector('#qrBoite'); return b.scrollHeight - b.clientHeight; }")
        assert haut <= 0, f"QR en grand à {largeur} px : il faut faire défiler ({haut} px)"
        for theme in ("light", "dark"):
            prof.emulate_media(color_scheme=theme)
            prof.screenshot(path=os.path.join(SORTIE, f"qr-grand-{largeur}-{theme}.png"))
        prof.emulate_media(color_scheme="light")
        prof.keyboard.press("Escape")
        prof.wait_for_selector("#qrBoite:not([open])", state="attached")
    prof.set_viewport_size({"width": 1440, "height": 900})
    code = prof.inner_text("#code").strip()
    tot = prof.evaluate("document.querySelector('#codeGrand').textContent")
    assert tot == code, (tot, code)
    prof.select_option("#duree", "0")
    prof.click("#commencer")
    premiere = next(i for i, d in enumerate(COURS["diapositives"]) if d["type"] == "question")
    suivante(prof, "#action", "#compteur", premiere)
    # pendant la question : la touche Q ouvre, puis referme ; les flèches ne font pas avancer le cours pendant ce temps
    prof.keyboard.press("q")
    prof.wait_for_selector("#qrBoite[open]")
    compteur = prof.inner_text("#compteur")
    prof.keyboard.press("ArrowRight")
    assert prof.inner_text("#compteur") == compteur, "le cours a avancé sous le QR code"
    prof.keyboard.press("q")
    prof.wait_for_selector("#qrBoite:not([open])", state="attached")
    # un·e élève en retard scanne le QR code : il ou elle arrive directement sur la question en cours
    e = ctx.new_page()
    e.set_viewport_size({"width": 320, "height": 740})
    surveiller(e, "en retard")
    e.goto(base + f"rejoindre.html?s={code}")
    e.fill("#champPseudo", "Retard")
    e.click("#rejoindre")
    e.wait_for_selector('button.option[data-choix="0"]:not([disabled])')
    attendre_texte(e, ".q-num", "Question 1 sur 20")
    e.click(f'button.option[data-choix="{BONNES[0]}"]')
    attendre_texte(e, "#envoyee", "reçue")
    attendre_texte(prof, "#statutQ", "Tout le monde a répondu")
    prof.click("#action")
    attendre_texte(e, "#points", "110 pts")
    print("  QR en grand : bouton et touche Q, à l'accueil et pendant une question (3 largeurs, 2 thèmes) ; élève en retard : question en cours, réponse reçue, points")
    ctx.close()


def puzzle_resoudre(page, lignes, indentation=True):
    """Remet le puzzle dans l'ordre avec les boutons (choisir une ligne, « Monter », « Indenter »)."""
    for p, sol in enumerate(lignes):
        textes = page.eval_on_selector_all(".puzzle .p-ligne code", "l => l.map(c => c.textContent)")
        cur = next(i for i in range(p, len(textes)) if textes[i] == sol.strip())
        page.locator(".puzzle .p-ligne").nth(cur).click()
        for _ in range(cur - p):
            page.click(".p-outils button:text-is('↑ Monter')")
        if indentation:
            for _ in range((len(sol) - len(sol.lstrip(" "))) // 4):
                page.click(".p-outils button:text-is('⇥ Indenter')")


def autres_types(nav, base):
    """Les autres types de questions en séance : nuage de mots, relier, puzzle de code, ligne fautive.
    Deux téléphones (320 px, clair et obscur) et la page projetée ; un espion écoute le canal."""
    with open(os.path.join(RACINE, "cours", "revision-conditions-boucles.json"), encoding="utf-8") as f:
        cours = json.load(f)
    diapos = cours["diapositives"]
    ou = {d["type"]: i for i, d in enumerate(diapos) if d["type"] in ("nuage", "relier", "puzzle", "ligne")}
    ctx = contexte(nav, base)
    # le piège à innerHTML : un mot du nuage marqué « motpiege » ne doit jamais passer par du HTML
    ctx.add_init_script(PIEGE.replace("XSSMARK", "motpiege"))
    prof = ctx.new_page()
    prof.set_viewport_size({"width": 1440, "height": 900})
    surveiller(prof, "autres types : enseignant·e")
    prof.goto(base + "animer.html?cours=revision-conditions-boucles")
    attendre_texte(prof, "#etatConnexion", "Séance ouverte")
    code = prof.inner_text("#code").strip()
    espion = ctx.new_page()
    espion.goto(base + "index.html")
    espion.evaluate("canal => { window.__vus = []; const bc = new BroadcastChannel('faux:' + canal); bc.onmessage = ({ data }) => { if (data.k === 'b') window.__vus.push(data.payload); }; }", "quizz-nsi:" + code)
    tel = []
    for pseudo, theme in (("Kobalt", "light"), ("Ixo", "dark")):
        e = ctx.new_page()
        e.set_viewport_size({"width": 320, "height": 740})
        e.emulate_media(color_scheme=theme)
        surveiller(e, "autres types : " + pseudo)
        e.goto(base + f"rejoindre.html?s={code}")
        e.fill("#champPseudo", pseudo)
        e.click("#rejoindre")
        tel.append(e)
    attendre_texte(prof, "#eleves", "Ixo")
    prof.select_option("#duree", "0")
    prof.click("#commencer")
    k, i = tel

    # ── le nuage de mots ──
    suivante(prof, "#action", "#compteur", ou["nuage"])
    for e, mot in ((k, "Répéter"), (i, "  motpiege   Répéter ")):
        e.wait_for_selector(".nuage-form input")
        e.fill(".nuage-form input", "<b>x</b>")
        e.click(".nuage-form button")
        attendre_texte(e, ".nuage-form .erreur-champ", "Seulement")  # filtré avant l'envoi
        e.fill(".nuage-form input", mot)
        e.click(".nuage-form button")
        attendre_texte(e, "#envoyee", "reçue")
    k.screenshot(path=os.path.join(SORTIE, "autres-nuage-320.png"), full_page=True)
    attendre_texte(prof, "#statutQ", "Tout le monde a répondu")
    attendre_texte(prof, ".zone-nuage", "2 mots reçus")
    assert "répéter" not in prof.inner_text("#scene").lower() and "motpiege" not in prof.inner_text("#scene"), "le nuage ne s'affiche qu'après « Montrer le nuage »"
    prof.click(".nuage-reglages button")
    prof.wait_for_selector("#motsBoite[open]")
    attendre_texte(prof, "#motsListe", "motpiege répéter")
    prof.evaluate("document.getElementById('motsBoite').close()")
    assert prof.inner_text("#action").startswith("Montrer le nuage")
    prof.click("#action")
    prof.wait_for_selector(".nuage .mot")
    assert sorted(prof.eval_on_selector_all(".nuage .mot", "l => l.map(b => b.textContent)")) == ["motpiege répéter", "répéter"], "deux mots, en minuscules, espaces réduits"
    for theme in ("light", "dark"):
        prof.emulate_media(color_scheme=theme)
        prof.screenshot(path=os.path.join(SORTIE, f"autres-nuage-1440-{theme}.png"))
    prof.emulate_media(color_scheme="light")
    prof.click(".nuage .mot:text-is('motpiege répéter')")  # l'enseignant·e masque un mot d'un clic
    prof.wait_for_function("() => document.querySelectorAll('.nuage .mot').length === 1")
    prof.select_option("#seuilNuage", "2")  # seulement les mots donnés par 2 élèves au moins
    attendre_texte(prof, ".zone-nuage", "Aucun mot donné par 2 élèves")
    attendre_texte(k, "#ecran", "Ton mot")
    attendre_texte(k, "#points", "0 pts")

    # ── relier ──
    rel = diapos[ou["relier"]]
    suivante(prof, "#action", "#compteur", ou["relier"])
    n = len(rel["paires"])
    for e, choix in ((k, list(range(n))), (i, [1, 0] + list(range(2, n)))):
        e.wait_for_selector(".relier select")
        for g, d in enumerate(choix):
            e.locator(".relier select").nth(g).select_option(str(d))
        e.click(".relier button.bouton.fort")
        attendre_texte(e, "#envoyee", "reçue")
    i.screenshot(path=os.path.join(SORTIE, "autres-relier-320-obscur.png"), full_page=True)
    attendre_texte(prof, "#statutQ", "Tout le monde a répondu")
    prof.click("#action")
    attendre_texte(prof, ".zone-correction", "1 sur 2")
    prof.screenshot(path=os.path.join(SORTIE, "autres-relier-1440.png"), full_page=True)
    attendre_texte(k, "#points", "110 pts")
    attendre_texte(i, "#points", f"{10 + round(100 * (n - 2) / n)} pts")  # 3 paires sur 5 : 60 points sur 100
    i.screenshot(path=os.path.join(SORTIE, "autres-relier-correction-320-obscur.png"), full_page=True)

    # ── puzzle de code ──
    pz = diapos[ou["puzzle"]]
    suivante(prof, "#action", "#compteur", ou["puzzle"])
    k.wait_for_selector(".puzzle .p-ligne")
    puzzle_resoudre(k, pz["lignes"])
    k.screenshot(path=os.path.join(SORTIE, "autres-puzzle-320.png"), full_page=True)
    k.click(".puzzle-zone button.bouton.fort")
    attendre_texte(k, "#envoyee", "reçue")
    prof.screenshot(path=os.path.join(SORTIE, "autres-puzzle-1440.png"), full_page=True)
    prof.click("#action")
    attendre_texte(prof, ".zone-correction", "1 sur 1")
    attendre_texte(k, "#points", "220 pts")

    # ── la ligne fautive ──
    lg = diapos[ou["ligne"]]
    suivante(prof, "#action", "#compteur", ou["ligne"])
    for e, l in ((k, lg["ligne"]), (i, 2)):
        e.wait_for_selector(".c-ligne")
        e.locator(".c-ligne").nth(l - 1).click()
        e.click(".lignes-zone button.bouton.fort")
        attendre_texte(e, "#envoyee", "reçue")
    attendre_texte(prof, "#statutQ", "Tout le monde a répondu")
    prof.click("#action")
    attendre_texte(prof, ".zone-correction", "1 sur 2")
    prof.screenshot(path=os.path.join(SORTIE, "autres-ligne-1440.png"), full_page=True)
    attendre_texte(k, "#points", "330 pts")
    attendre_texte(i, "#ecran", "total = 0")
    attendre_texte(i, "#ecran", lg["pieges"]["2"].split("`")[0].strip())
    i.screenshot(path=os.path.join(SORTIE, "autres-ligne-correction-320-obscur.png"), full_page=True)
    attendre_texte(i, "#points", f"{10 + round(100 * (n - 2) / n) + 10} pts")

    for pg in (prof, k, i):
        assert not pg.evaluate("window.__piege"), f"un mot du nuage est passé par du HTML : {pg.evaluate('window.__piege')[:3]}"
    # ce que l'espion a vu : aucun mot du nuage, aucune réponse en clair
    vus = espion.evaluate("window.__vus")
    for m in vus:
        t = json.dumps(m, ensure_ascii=False).lower()
        assert "répéter" not in t and "motpiege" not in t, f"un mot du nuage est passé en clair : {t[:120]}"
        if m.get("t") == "rep":
            assert set(m) == {"t", "de", "iv", "donnees"}
    assert any(m.get("t") == "corrige" for m in vus)
    print(f"  autres types : nuage (filtré, caché puis montré, mot masqué), relier (60 points pour 3 paires sur 5), puzzle, ligne fautive ; {len(vus)} messages écoutés, aucun mot ni réponse en clair")
    ctx.close()


def sans_chiffrement(nav, base):
    """Un téléphone qui ne sait pas chiffrer le dit tout de suite ; un accusé qui ne vient pas est signalé."""
    for nom, script in (("sans crypto.subtle", "Object.defineProperty(window.crypto, 'subtle', { get: () => undefined });"),
                        ("génération en échec", "crypto.subtle.generateKey = () => Promise.reject(new Error('refus'));")):
        ctx = contexte(nav, base)
        ctx.add_init_script(script)
        p = ctx.new_page()
        surveiller(p, nom)
        p.goto(base + "rejoindre.html?s=ABCD")
        p.fill("#champPseudo", "Ixo")
        p.click("#rejoindre")
        attendre_texte(p, "#ecran", "Ce navigateur ne peut pas participer à la séance en direct")
        assert p.locator('#ecran a[href="revision.html"]').count() == 1
        ctx.close()
    # une page projetée qui ne répond jamais : « reçue » ne s'affiche pas, un message le dit
    ctx = contexte(nav, base)
    p = ctx.new_page()
    surveiller(p, "accusé absent")
    p.goto(base + "rejoindre.html?s=WXYZ")
    p.fill("#champPseudo", "Ixo")
    p.click("#rejoindre")
    faux = ctx.new_page()
    faux.goto(base + "index.html")
    faux.evaluate("""async () => {
        const k = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, false, ['deriveKey']);
        const j = await crypto.subtle.exportKey('jwk', k.publicKey);
        const bc = new BroadcastChannel('faux:quizz-nsi:WXYZ');
        const info = { id: '9999999999999999', role: 'hote', cle: { x: j.x, y: j.y } };
        bc.onmessage = ({ data }) => { if (data.k === 'p' && data.info.id !== info.id) bc.postMessage({ k: 'p', cle: info.id, info }); };
        bc.postMessage({ k: 'p', cle: info.id, info });
        setTimeout(() => bc.postMessage({ k: 'b', event: 'm', payload: { t: 'question', cours: 'piles-files', qid: 'q01', reste: null, duree: 0, ferme: false } }), 500);
    }""")
    p.wait_for_selector('button.option[data-choix="1"]:not([disabled])')
    p.click('button.option[data-choix="1"]')
    attendre_texte(p, "#envoyee", "choisie")
    attendre_texte(p, "#envoyee", "n'a pas encore reçu", delai=15000)
    assert "reçue par" not in p.inner_text("#envoyee")
    print("  sans chiffrement : message clair (2 cas) ; accusé absent signalé, jamais « reçue »")
    ctx.close()


def stockage(nav, base):
    """L'entrée « eleve » (code, pseudo, identifiant) périmée est effacée au chargement de chaque page."""
    ctx = contexte(nav, base)
    p = ctx.new_page()
    surveiller(p, "stockage")
    for page in ("index.html", "revision.html", "animer.html", "rejoindre.html", "imprimer.html"):
        p.goto(base + "index.html")
        p.evaluate("() => localStorage.setItem('quizz-nsi:eleve', JSON.stringify({ id: '0123456789abcdef', pseudo: 'Ixo', code: 'ABCD', jusqua: Date.now() - 1000 }))")
        p.goto(base + page)
        p.wait_for_timeout(200)
        assert p.evaluate("localStorage.getItem('quizz-nsi:eleve')") is None, f"{page} : entrée périmée gardée"
    # une entrée valide est gardée, et préremplit la page élève
    p.evaluate("() => localStorage.setItem('quizz-nsi:eleve', JSON.stringify({ id: '0123456789abcdef', pseudo: 'Ixo', code: 'ABCD', jusqua: Date.now() + 3600000 }))")
    p.goto(base + "rejoindre.html")
    assert p.input_value("#champPseudo") == "Ixo"
    print("  stockage : entrée périmée effacée sur les 5 pages, entrée valide gardée")
    ctx.close()


def autonome(nav, base):
    ctx = contexte(nav, base)
    p = ctx.new_page()
    p.set_viewport_size({"width": 390, "height": 800})
    surveiller(p, "autonome")
    p.goto(base + "revision.html?cours=piles-files")
    p.wait_for_selector("section.d-titre")
    k = 0
    for i, d in enumerate(COURS["diapositives"]):
        if i > 0:
            suivante(p, "#suiv", "#compteur", i)
        if d["type"] == "question":
            p.wait_for_selector(f'section.d-question[data-q="{k + 1}"]')
            if k == 0:  # une erreur d'abord : feedback, puis nouvel essai
                p.click(f'button.option[data-choix="{(BONNES[k] + 1) % 4}"]')
                attendre_texte(p, ".zone-correction", "Pas encore")
                p.screenshot(path=os.path.join(SORTIE, "autonome-erreur-390.png"), full_page=True)
            p.keyboard.press("abcd"[BONNES[k]])  # au clavier
            attendre_texte(p, ".zone-correction", "Bonne réponse")
            k += 1
    attendre_texte(p, "#scene", "19 sur 20")
    p.screenshot(path=os.path.join(SORTIE, "autonome-bilan-390.png"), full_page=True)
    p.reload()  # la progression reste sur l'appareil
    attendre_texte(p, "#scene", "19 sur 20")
    print(f"  autonome : {len(COURS['diapositives'])} diapositives, apparitions progressives, bilan 19 sur 20 du premier coup")
    ctx.close()


def rejouer(nav, base):
    """Rejouer le quiz seul·e : les questions dans un autre ordre, les réponses mélangées, rien d'envoyé."""
    ctx = contexte(nav, base)
    p = ctx.new_page()
    p.set_viewport_size({"width": 320, "height": 740})
    surveiller(p, "rejouer")
    envois = []
    p.on("request", lambda r: envois.append(r.url) if r.method != "GET" else None)
    p.goto(base + "revision.html?cours=piles-files&rejouer")
    p.wait_for_selector("section.d-titre")
    assert not p.is_visible("#questionsSeules")
    juste_de = {}
    for q in QUESTIONS:
        o = q["options"][BONNES[QUESTIONS.index(q)]]
        juste_de[q["nom"].replace("`", "")] = (o.get("texte") or " ".join(o.get("code", []))).replace("`", "")
    noms, places = [], []
    p.click("#suiv")
    for k in range(20):
        p.wait_for_selector(f'section.d-question[data-q="{k + 1}"]')
        nom = p.inner_text(".q-nom").strip()
        noms.append(nom)
        bonne = juste_de[nom]
        labels = p.eval_on_selector_all("button.option", "l => l.map(b => b.getAttribute('aria-label'))")
        i = next(i for i, l in enumerate(labels) if l.endswith(": " + bonne))
        places.append(i)
        if k == 0:
            p.click(f'button.option[data-choix="{(i + 1) % 4}"]')
            attendre_texte(p, ".zone-correction", "Pas encore")
            p.screenshot(path=os.path.join(SORTIE, "rejouer-question-320.png"), full_page=True)
        p.click(f'button.option[data-choix="{i}"]')
        attendre_texte(p, ".zone-correction", "Bonne réponse")
        p.click("#suiv")
    attendre_texte(p, "#scene", "19 sur 20")
    p.screenshot(path=os.path.join(SORTIE, "rejouer-bilan-320.png"), full_page=True)
    originaux = [q["nom"].replace("`", "") for q in QUESTIONS]
    assert sorted(noms) == sorted(originaux) and noms != originaux, "les 20 questions, dans un autre ordre"
    assert places != BONNES, "les réponses sont mélangées"
    # le même ordre après un rechargement (onglet), un nouvel ordre avec « Rejouer encore »
    p.reload()
    attendre_texte(p, "#scene", "19 sur 20")
    assert p.evaluate("Object.keys(localStorage).filter(k => k.includes('rejouer'))") == [], "rien dans le stockage durable"
    p.click("#recommencer")
    p.wait_for_selector("section.d-titre")
    p.click("#suiv")
    autre = p.inner_text(".q-nom").strip()
    p.wait_for_timeout(100)
    assert not envois, f"des données sont parties : {envois}"
    print(f"  rejouer : 20 questions mélangées (la 1re était {noms[0][:30]}…, puis {autre[:30]}…), réponses mélangées, rien d'envoyé, rien de durable")
    ctx.close()


def autonome_autres(nav, base):
    """Les autres types en révision : essais illimités, ce qui est juste est marqué, le bilan les compte."""
    with open(os.path.join(RACINE, "cours", "revision-conditions-boucles.json"), encoding="utf-8") as f:
        diapos = json.load(f)["diapositives"]
    ou = {d["type"]: i + 1 for i, d in enumerate(diapos) if d["type"] in ("nuage", "relier", "puzzle", "ligne")}
    ctx = contexte(nav, base)
    p = ctx.new_page()
    p.set_viewport_size({"width": 320, "height": 740})
    surveiller(p, "autonome, autres types")
    url = base + "revision.html?cours=revision-conditions-boucles#"
    p.goto(url + str(ou["nuage"]))
    p.wait_for_selector(".nuage-form input")
    p.fill(".nuage-form input", "répéter")
    p.click(".nuage-form button")
    attendre_texte(p, ".zone-correction", "Merci")
    p.goto(url + str(ou["relier"])); p.reload()
    p.wait_for_selector(".relier select")
    n = len(diapos[ou["relier"] - 1]["paires"])
    for choix in ([1, 0] + list(range(2, n)), list(range(n))):
        for g, d in enumerate(choix):
            p.locator(".relier select").nth(g).select_option(str(d))
        p.click(".relier button.bouton.fort")
    attendre_texte(p, ".zone-correction", "Tout est bien relié")
    p.screenshot(path=os.path.join(SORTIE, "autonome-relier-320.png"), full_page=True)
    p.goto(url + str(ou["puzzle"])); p.reload()
    p.wait_for_selector(".puzzle .p-ligne")  # le cours se charge après la page
    puzzle_resoudre(p, diapos[ou["puzzle"] - 1]["lignes"])
    p.click(".puzzle-zone button.bouton.fort")
    attendre_texte(p, ".zone-correction", "remis en ordre")
    p.goto(url + str(ou["ligne"])); p.reload()
    p.wait_for_selector(".c-ligne")
    p.locator(".c-ligne").nth(1).click(); p.click(".lignes-zone button.bouton.fort")
    attendre_texte(p, ".zone-correction", "Pas encore")
    p.screenshot(path=os.path.join(SORTIE, "autonome-ligne-erreur-320.png"), full_page=True)
    p.locator(".c-ligne").nth(diapos[ou["ligne"] - 1]["ligne"] - 1).click(); p.click(".lignes-zone button.bouton.fort")
    attendre_texte(p, ".zone-correction", "Bien vu")
    p.goto(url + str(len(diapos))); p.reload()
    attendre_texte(p, "#scene", "Les autres questions : 1 sur 3")
    print("  autonome, autres types : nuage, relier (2 essais), puzzle, ligne fautive (2 essais) ; bilan 1 sur 3 du premier coup")
    ctx.close()


def impression(nav, base):
    ctx = contexte(nav, base)
    p = ctx.new_page()
    surveiller(p, "impression")
    for nom, q in (("sujet", "piles-files"), ("corrige", "piles-files&corrige"), ("sujet-revision", "revision-conditions-boucles"), ("corrige-revision", "revision-conditions-boucles&corrige")):
        p.goto(base + "imprimer.html?cours=" + q)
        p.wait_for_selector(".f-question")
        p.emulate_media(media="print")
        p.set_viewport_size({"width": 702, "height": 1000})  # largeur utile d'une page A4 (186 mm)
        deborde = p.evaluate("""() => { const f = document.querySelector('.feuille').getBoundingClientRect();
            return [...document.querySelectorAll('.feuille *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.right > f.right + 1; }).map(e => e.tagName + '.' + e.className).slice(0, 5); }""")
        assert not deborde, f"{nom} déborde : {deborde}"
        chemin = os.path.join(SORTIE, f"imprimer-{nom}.pdf")
        p.pdf(path=chemin, format="A4", prefer_css_page_size=True, print_background=True)
        p.emulate_media(media="screen")
        print(f"  impression : {nom} sans débordement ({chemin})")
    ctx.close()


def rendus(nav, base):
    pages = ["index.html", "revision.html#7", "revision.html#30", "revision.html?rejouer", "revision.html?cours=revision-conditions-boucles#10",
             "revision.html?cours=revision-conditions-boucles#18", "revision.html?cours=revision-conditions-boucles#33", "revision.html?cours=revision-conditions-boucles&rejouer", "animer.html", "rejoindre.html", "imprimer.html", "imprimer.html?corrige"]
    for theme in ("light", "dark"):
        for largeur in (320, 768, 1440):
            ctx = contexte(nav, base, color_scheme=theme, viewport={"width": largeur, "height": 900})
            for adresse in pages:
                p = ctx.new_page()
                surveiller(p, f"{adresse} {largeur} {theme}")
                p.goto(base + adresse)
                p.wait_for_timeout(500)
                large = p.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                assert large <= 0, f"{adresse} à {largeur} px ({theme}) : défilement horizontal de {large} px"
                nom = adresse.replace(".html", "").replace("#", "-").replace("?", "-")
                p.screenshot(path=os.path.join(SORTIE, f"rendu-{nom}-{largeur}-{theme}.png"), full_page=True)
                p.close()
            ctx.close()
    print("  rendus : 12 pages × 3 largeurs × 2 thèmes, sans défilement horizontal")


def main():
    s, base = serveur()
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        seance(nav, base)
        injection(nav, base)
        qr_et_retard(nav, base)
        autres_types(nav, base)
        stockage(nav, base)
        sans_chiffrement(nav, base)
        autonome(nav, base)
        rejouer(nav, base)
        autonome_autres(nav, base)
        impression(nav, base)
        rendus(nav, base)
        nav.close()
    s.shutdown()
    if externes:
        print("Requêtes externes bloquées :", sorted(set(externes)))
    if erreurs:
        print("Erreurs JavaScript :", *erreurs, sep="\n  ")
    ok = not erreurs and not externes
    print("parcours : " + ("tout est conforme" if ok else "ÉCHEC") + f" ; captures dans {SORTIE}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
