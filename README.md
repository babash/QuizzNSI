# 🎯 QuizzNSI

**Un cours court en diapositives et des questions tout de suite, sur le téléphone de chaque élève.** Pour la NSI de première et de terminale.

> Tes élèves rejoignent la séance avec un QR code et un prénom ou un pseudo. Le cours avance au tableau, une notion par diapositive ; à chaque question, chacun·e répond depuis son téléphone et lit aussitôt l'explication de sa réponse, juste ou fausse. Après une erreur, l'explication dit pourquoi, et le « rebond » récompense la bonne réponse suivante. Le même cours se révise seul·e à la maison et s'imprime sur papier.

## 👉 [Essayer maintenant : babash.github.io/QuizzNSI](https://babash.github.io/QuizzNSI/)

**Gratuit · sans compte · rien à installer · aussi sur téléphone · rien n'est enregistré en ligne ; le prénom ou le pseudo passe seulement en direct dans la séance**

QuizzNSI fait partie des [Ressources NSI et SNT](https://babash.github.io/Babash-NSI-SNT/), rubrique [NSI Terminale](https://babash.github.io/Babash-NSI-SNT/nsi-terminale/). Il a d'abord été développé dans le dépôt du site, dont il garde l'historique ; les anciennes adresses redirigent ici.

---

## Une séance en trois étapes

1. **Tu** ouvres [la page d'animation](https://babash.github.io/QuizzNSI/animer.html?cours=piles-files) et la projettes : un code de 4 lettres, un lien et un QR code s'affichent. Tu choisis le temps par question (sans minuterie, ou de 20 s à 1 min 30) et le classement (à la fin, après chaque question, ou aucun).
2. **Les élèves** rejoignent avec le QR code, le lien ou le code, depuis un téléphone ou un ordinateur, avec un prénom ou un pseudo (jamais un nom de famille). Un pseudo déplacé se retire d'un clic : l'élève en choisit un autre. À tout moment, **QR code en grand** (ou la touche **Q**) affiche le QR code et le code de la séance en très grand, lisibles du fond de la classe ; Q ou Échap les referme. Un·e élève en retard rejoint en cours de route : son téléphone arrive directement sur la diapositive ou la question en cours.
3. **Tu avances dans le cours** (flèches, Entrée), environ 45 minutes, ou deux fois 20 : les téléphones suivent les diapositives ; à chaque question, l'écran compte les réponses, puis **Montrer la réponse** affiche la répartition, l'erreur la plus fréquente avec son explication, et le feedback de chaque option.

**À la fin de la séance, le quiz se rejoue.** Le téléphone de chaque élève propose « Rejouer le quiz seul·e », et la page projetée affiche un QR code « rejouer » (dans le podium, et en grand avec la touche Q) : chacun·e rejoue les questions sans l'enseignant·e, dans un nouvel ordre et avec les réponses mélangées, corrigées tout de suite. Rien n'est envoyé ; l'ordre et les réponses restent dans l'onglet du téléphone, effacés à sa fermeture. Le lien : `revision.html?cours=<id>&rejouer`.

Tu veux d'abord découvrir QuizzNSI seul·e ? Ouvre l'animation [en mode démo](https://babash.github.io/QuizzNSI/animer.html?cours=piles-files&demo) : la séance passe alors entre les onglets de ton navigateur. Le [mode autonome](https://babash.github.io/QuizzNSI/revision.html?cours=piles-files) sert à réviser seul·e ; [les questions à imprimer](https://babash.github.io/QuizzNSI/imprimer.html?cours=piles-files) ont [leur corrigé](https://babash.github.io/QuizzNSI/imprimer.html?cours=piles-files&corrige) à part.

Une seule page projetée par séance : si une deuxième est ouverte (onglet dupliqué, autre ordinateur), la page avertit. Sans réseau, la page d'animation marche comme un simple diaporama, et la page élève propose le mode autonome.

## Ce que font les élèves

Le premier cours, **piles et files**, commence par se demander pourquoi : des scènes du quotidien à Mayotte (la boîte de chips en tube, la file au doukabé, le bouchon jusqu'à Mamoudzou), puis deux programmes de tous les jours (le bouton « Annuler », l'imprimante de la salle info). Un essai avec une liste Python devient vite pénible, une diapositive d'humour le dit… et la pile et la file arrivent comme la solution : des structures qui imposent leur règle.

Le second, **« Conditions, boucles, fonctions »** (Première), est une séance de révision : pas de cours, mais [4 blocs de 5 questions](https://babash.github.io/QuizzNSI/animer.html?cours=revision-conditions-boucles) (les conditions, la boucle `for`, la boucle `while`, les fonctions). À la fin de chaque bloc, chaque élève note son score sur sa feuille de route : le quiz sert de bilan avant un contrôle.

**De nouveaux types de questions**, en plus des questions à choix : le **nuage de mots** (chaque élève propose autant de mots qu'il ou elle veut ; quand l'enseignant·e montre le nuage, il s'affiche au tableau et sur les téléphones, où l'on vote pour les mots des camarades ; l'enseignant·e supprime un mot à tout moment ; non noté), **relier** (un terme et sa définition, un code et sa sortie), le **puzzle de code** (remettre les lignes dans l'ordre et à la bonne indentation) et **la ligne fautive** (toucher la ligne qui contient l'erreur). Un cours de démonstration en a un de chaque : [demo-types-de-questions](https://babash.github.io/QuizzNSI/animer.html?cours=demo-types-de-questions) (les cours de classe gardent leurs 20 questions à choix). Chacun marche au téléphone (320 px, au clavier et au lecteur d'écran), sur la page projetée, en révision et sur papier ; son code est exécuté par le vérificateur ([le format](cours/FORMAT.md#les-autres-types-de-questions)).

Viennent ensuite les définitions (structure de données, structure linéaire, interface et implémentation), la pile, la file, Python, et pour aller plus loin. Les 20 questions sont placées là où elles font pratiquer :

| Étape | Ce que les élèves font |
|---|---|
| Reconnaître | pile ou file ? quel élément sort en premier ? |
| Suivre | l'état d'une pile ou d'une file après une suite d'opérations (`empiler`, `depiler`, `sommet`, `enfiler`, `defiler`, `tete`) |
| Analyser | une fonction qui compte les éléments d'une pile, une file faite de deux piles, un vérificateur de parenthèses |
| Trouver l'erreur | une boucle qui dépile trop, retirer le mauvais élément d'une liste, une fonction qui doit lire une pile sans la modifier |

Chaque question a un objectif affiché, quatre options tirées d'erreurs fréquentes et un feedback pour chacune. Chaque code affiché a été exécuté par le vérificateur.

## Pour quels usages

| Usage | Comment |
|---|---|
| **Une séance en classe** (≈ 45 min, ou deux fois 20) | La page d'animation projetée, les téléphones des élèves. |
| **En îlots** | Un téléphone pour deux ou pour l'îlot : on se met d'accord avant de répondre. |
| **Pour s'entraîner seul·e** | Le mode autonome : les diapositives et les questions, des essais illimités, la correction quand on veut ; « Questions seules » saute les notions. |
| **Pour rejouer après la séance** | « Rejouer le quiz » : les questions seules, dans un nouvel ordre, les réponses mélangées ; « Rejouer encore » tire un autre ordre. |
| **Sur papier** | Les questions sur une feuille A4 en noir et blanc, le corrigé à part. |

## Pourquoi ça marche

- **Le pourquoi avant la définition** : la notion arrive comme la réponse à un problème que la classe a senti.
- **Un cours court, beaucoup de pratique** : une notion par diapositive, puis une question qui la fait pratiquer.
- **Les erreurs expliquées, la correction immédiate** : chaque option a son explication, montrée tout de suite ; en révision, les essais sont illimités.
- **La progression valorisée** : le rebond récompense la bonne réponse qui suit une erreur ; le podium compte peu et n'apparaît qu'à la fin.
- **Entraide en îlots** : un téléphone pour deux ou pour l'îlot, et le débat avant de répondre.

## Données des élèves

- **Enregistré en ligne** (canaux temps réel de Supabase, sans aucune table) : rien. Le prénom ou le pseudo et les réponses passent en direct dans la séance, sans être gardés en ligne. Pas d'adresse électronique, pas de nom de famille.
- **Visible par les autres** : pendant la séance seulement, ce que montre l'écran projeté (les pseudos présents, la répartition des réponses, les rebonds, le podium quand il est affiché, et les mots du nuage, sans les pseudos, au tableau et sur les téléphones, quand l'enseignant·e montre le nuage). Les réponses partent chiffrées pour la page projetée ; une fausse page projetée, ouverte par quelqu'un qui connaît le code, les reçoit aussi (voir les risques acceptés, [docs/DONNEES.md](docs/DONNEES.md)).
- **Le nuage de mots** : le seul texte libre d'élève qui circule. Les mots partent chiffrés vers la page projetée ; rien ne s'affiche avant « Montrer le nuage » ; ensuite, les mots du tableau (jamais leur auteur·rice) partent en clair vers les téléphones de la classe, qui votent. Chaque mot est filtré (un ou deux mots, sans caractère spécial) et affiché comme du texte ; l'enseignant·e supprime un mot à tout moment, partout. Rien n'est gardé, ni en ligne ni sur les téléphones. Le filtre ne juge pas le sens : un mot déplacé s'affiche jusqu'à sa suppression (risques décrits dans [docs/DONNEES.md](docs/DONNEES.md)).
- **Sur l'appareil** : le code de séance, le pseudo, un identifiant, les réponses et les points de la séance (pas les mots ni les voix du nuage), effacés à la fin de la séance, et sinon au premier chargement d'une page de QuizzNSI après 12 heures ; en révision, les réponses du mode autonome ; pour rejouer le quiz, l'ordre tiré et les réponses, dans l'onglet seulement (effacés à sa fermeture).
- **Pour effacer** : rien à effacer en ligne ; sur l'appareil, « Quitter » ou « Recommencer à zéro », ou l'effacement des données du navigateur.

Le détail : [docs/DONNEES.md](docs/DONNEES.md).

## Le barème

| Action | Points | Pourquoi |
|---|---|---|
| Répondre, même faux | +10 | oser répondre |
| Bonne réponse | +100 | l'essentiel : réfléchir |
| Rapidité (avec une minuterie, et seulement si c'est juste) | de +20 à 0 | un peu d'élan, sans écraser la réflexion |
| Rebond : une bonne réponse juste après une erreur | +30 | valoriser la progression, pas seulement les meilleur·e·s |

Les autres types de questions : **relier** et **puzzle de code** rapportent la bonne réponse en proportion de ce qui est juste (3 paires sur 5 : +60 au lieu de +100 ; rapidité et rebond seulement si tout est juste) ; **la ligne fautive** se note comme une question à choix ; **le nuage de mots** n'est pas noté (il n'a pas de bonne réponse).

Chaque téléphone calcule ses propres points ; la page projetée fait seule foi pour le podium. La place d'un·e élève n'est connue que s'il ou elle est sur le podium affiché.

## Pour aller plus loin

| Document | Contenu |
|---|---|
| [Installer sa copie](docs/INSTALLER.md) | la publication par GitHub Pages, le projet Supabase des séances, le mode démo |
| [Données et sécurité](docs/DONNEES.md) | ce qui est gardé, où, combien de temps ; ce que diffuse une séance ; les risques acceptés |
| [Architecture](docs/ARCHITECTURE.md) | le code, ajouter un cours, les tests |
| [Le format des cours](cours/FORMAT.md) | écrire un cours-quiz : diapositives, questions, schémas, vérifications |

## Feuille de route

- **Un cours-quiz par fiche de FichesNSI** (22 fiches), sur le modèle de piles et files ;
- **Un essai en classe**, pour régler le temps par question et le barème ;
- **Les cours de SNT**, avec les compétences Pix explicitées.

## Contact

Conçu par Babash - NSI Tani Malandi pour les classes de NSI de première et de terminale de l'académie de Mayotte, développé avec l'aide de l'IA ([Claude Code](https://claude.com/claude-code)).
Une question, une idée, un bug ? Les [issues GitHub](https://github.com/babash/QuizzNSI/issues) du dépôt. Toutes les ressources sont sur le site [Ressources NSI et SNT](https://babash.github.io/Babash-NSI-SNT/).

## Licence

- **Le code** (les fichiers `.html`, `.css`, `.js` et `.py`, hors bibliothèques et polices) est sous licence [MIT](LICENSE).
- **Les documents** (les cours de `cours/`, ce README, `cours/FORMAT.md` et `docs/`) sont sous licence [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr).
- **Les bibliothèques** de `vendor/` (le client temps réel de [Supabase](https://supabase.com), [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) de Kazuhiko Arase) : licence MIT, notices dans [vendor/LICENCES-BIBLIOTHEQUES.txt](vendor/LICENCES-BIBLIOTHEQUES.txt). « QR Code » est une marque déposée de DENSO WAVE.
- **Les polices** Chakra Petch, JetBrains Mono et Atkinson Hyperlegible, intégrées dans `css/polices.css` : licence SIL OFL 1.1, copyrights et texte dans [css/LICENCE-POLICES.txt](css/LICENCE-POLICES.txt).

Tu peux les réutiliser et les modifier, y compris pour tes classes, en mentionnant Babash - NSI Tani Malandi et la licence ; un document modifié se partage sous la même licence. Si tu utilises l'IA pour les modifier, merci de le préciser.
