/* QuizzNSI : le rendu des diapositives et des questions (MIT, Babash - NSI Tani Malandi).
   Les mêmes fonctions servent à la page projetée, au mode autonome et à la version imprimable. */
(function (racine) {
  'use strict';
  const Q = racine.QuizzNSI;
  const t = Q.texte, e = Q.echapper;

  const liste = (items, cl, frag) => '<ul class="' + (cl || '') + '">' + items.map(x => '<li' + (frag ? ' class="frag"' : '') + '>' + t(x) + '</li>').join('') + '</ul>';
  // Un bloc de code « révélé au clic » : caché derrière un fragment (il apparaît à l'étape suivante).
  const code = (d, lignes) => d.code_cache ? '<div class="frag code-cache">' + Q.blocCode(lignes) + '</div>' : Q.blocCode(lignes);
  const consigne = d => d.consigne ? '<div class="consigne frag"><p class="c-titre">À toi</p>' + liste(d.consigne, 'puces') + '</div>' : '';

  /* Les apparitions progressives : les éléments .frag d'une diapositive sont cachés, puis montrés un
     à un (page projetée, mode autonome) ; le téléphone suit la page projetée. */
  Q.nbFragments = racineDiapo => racineDiapo.querySelectorAll('.frag').length;
  Q.montrerFragments = function (racineDiapo, k) {
    racineDiapo.querySelectorAll('.frag').forEach((e, i) => e.classList.toggle('vu', i < k));
  };

  Q.rendreOptions = function (q, opts) {
    opts = opts || {};
    return '<div class="options" role="' + (opts.boutons ? 'group' : 'list') + '" aria-label="Les quatre réponses possibles">' + q.options.map((o, i) => {
      const contenu = Q.pastille(i) + '<span class="opt-texte">' + (o.texte ? t(o.texte) : '') + (o.code ? Q.blocCode(o.code, { numeros: false }) : '') + '</span>';
      const lib = 'Réponse ' + Q.LETTRES[i] + ' (' + Q.NOMS_FORMES[i] + ')';
      return opts.boutons
        ? '<button type="button" class="option o' + i + '" data-choix="' + i + '" aria-label="' + e(lib) + ' : ' + e((o.texte || o.code.join(' ')).replace(/`/g, '')) + '">' + contenu + '</button>'
        : '<div class="option o' + i + '" role="listitem" data-choix="' + i + '">' + contenu + '</div>';
    }).join('') + '</div>';
  };

  Q.rendreEnonce = function (q, total) {
    return '<header class="q-tete"><p class="q-num">Question ' + q.numero + ' sur ' + total + '</p><h2 class="q-nom">' + t(q.nom) + '</h2>'
      + '<p class="objectif"><span>Objectif</span> ' + t(q.objectif) + '</p></header>'
      + '<div class="q-corps"><div class="q-texte">' + q.enonce.map(p => '<p>' + t(p) + '</p>').join('')
      + (q.code ? Q.blocCode(q.code) : '') + Q.console(q.console) + '</div>' + (q.schema ? Q.schema(q.schema) : '') + '</div>';
  };

  Q.rendreTrace = function (tr) {
    if (!tr) return '';
    return '<div class="trace"><table><caption>Trace pas à pas</caption><thead><tr>' + tr.colonnes.map(c => '<th scope="col">' + t(c) + '</th>').join('') + '</tr></thead><tbody>'
      + tr.lignes.map(l => '<tr>' + l.map((c, i) => i ? '<td>' + t(c) + '</td>' : '<th scope="row">' + t(c) + '</th>').join('') + '</tr>').join('') + '</tbody></table></div>';
  };

  // La correction d'une question : la réponse choisie (ou rien), la bonne réponse, l'explication,
  // puis le feedback de chaque option.
  Q.rendreCorrection = function (q, choix, opts) {
    opts = opts || {};
    const b = q.bonne, juste = choix === b;
    let h = '';
    if (choix != null) {
      h += '<div class="verdict ' + (juste ? 'ok' : 'ko') + '" role="status"><span class="symbole" aria-hidden="true">' + (juste ? '✓' : '✗') + '</span><div><p class="v-titre">'
        + (juste ? 'Bonne réponse' : 'Ta réponse : ' + Q.LETTRES[choix] + '. La bonne réponse est ' + Q.LETTRES[b] + '.') + '</p><p>' + t(q.options[choix].feedback) + '</p></div></div>';
    } else if (!opts.projection) {
      h += '<div class="verdict neutre" role="status"><span class="symbole" aria-hidden="true">•</span><div><p class="v-titre">La bonne réponse est ' + Q.LETTRES[b] + '.</p></div></div>';
    }
    h += '<p class="explication"><span>À retenir</span> ' + t(q.explication) + '</p>';
    h += Q.rendreTrace(q.trace);
    const fbs = '<ol class="feedbacks">' + q.options.map((o, i) => '<li class="' + (i === b ? 'bonne' : '') + '">' + Q.pastille(i) + '<div><p class="fb-titre">' + (i === b ? 'Bonne réponse' : 'Erreur fréquente') + '</p><p>' + t(o.feedback) + '</p></div></li>').join('') + '</ol>';
    h += opts.tousOuverts ? fbs : '<details class="autres"><summary>Lire l\'explication de chaque réponse</summary>' + fbs + '</details>';
    return h;
  };

  /* ── Les autres types de questions (js/activites.js) ──
     Le rendu « fixe » : la page projetée, la version imprimable, et l'énoncé sur le téléphone. Tout vient du
     fichier du cours ; aucune réponse d'élève ne passe par ici. */
  const A = () => Q.activites;
  Q.rendreEnonceActivite = function (d) {
    return '<header class="q-tete"><p class="q-num">' + e(A().NOMS[d.type]) + (d.type === 'nuage' ? ' · non noté' : '') + '</p><h2 class="q-nom">' + t(d.nom) + '</h2>'
      + '<p class="objectif"><span>Objectif</span> ' + t(d.objectif) + '</p></header>'
      + '<div class="q-corps"><div class="q-texte">' + d.enonce.map(p => '<p>' + t(p) + '</p>').join('')
      + (d.code && d.type !== 'ligne' ? Q.blocCode(d.code) + Q.console(d.console) : '') + '</div></div>';
  };
  // Les éléments à relier, à remettre dans l'ordre ou à toucher, sans réponse (projection, impression).
  Q.rendreElements = function (d, opts) {
    opts = opts || {};
    if (d.type === 'relier') {
      const o = A().ordreDroite(d);
      return '<div class="relier-fixe"><ol class="r-gauche">' + d.paires.map((p, i) => '<li><span class="r-num">' + (i + 1) + '</span><span>' + t(p.gauche) + '</span>' + (opts.papier ? '<span class="r-blanc">→ ……</span>' : '') + '</li>').join('')
        + '</ol><ol class="r-droite">' + o.map((k, j) => '<li><span class="r-num">' + Q.LETTRES_LONGUES[j] + '</span><span>' + t(d.paires[k].droite) + '</span></li>').join('') + '</ol></div>';
    }
    if (d.type === 'puzzle') {
      const o = A().ordrePuzzle(d), ind = A().avecIndent(d);
      return '<ol class="puzzle-fixe">' + o.map((k, j) => '<li><span class="r-num">' + Q.LETTRES_LONGUES[j] + '</span><code class="py">' + Q.colorerLigne(ind ? d.lignes[k].trim() : d.lignes[k]) + '</code></li>').join('') + '</ol>'
        + (ind ? '<p class="aide-act">Les lignes sont données sans leur indentation.</p>' : '');
    }
    if (d.type === 'ligne') return Q.blocCode(d.code, { numeros: true, marques: opts.marques }) + Q.console(d.console);
    if (d.type === 'nuage') return '<div class="zone-nuage" aria-live="polite"></div>';
    return '';
  };
  Q.rendreActivite = function (cours, d, opts) {
    opts = opts || {};
    return '<section class="diapo d-question d-activite d-' + e(d.type) + '" data-act="' + e(d.id) + '">' + Q.rendreEnonceActivite(d)
      + '<div class="zone-options">' + (opts.interactif ? '' : Q.rendreElements(d)) + '</div><div class="zone-correction" aria-live="polite"></div></section>';
  };

  /* La correction d'une question d'un autre type. r : la réponse de l'élève (sur son téléphone ou en révision),
     déjà contrôlée par Q.activites.valider, ou null (page projetée). Le mot d'un nuage n'est jamais écrit ici :
     la page qui l'affiche le met par textContent. */
  Q.rendreCorrectionActivite = function (d, r, opts) {
    opts = opts || {};
    const note = r == null ? null : A().noter(d, r);
    let h = '';
    const verdict = (ok, titre, texte) => '<div class="verdict ' + (ok === null ? 'neutre' : ok ? 'ok' : 'ko') + '" role="status"><span class="symbole" aria-hidden="true">' + (ok === null ? '•' : ok ? '✓' : '✗') + '</span><div><p class="v-titre">' + titre + '</p>' + (texte ? '<p>' + texte + '</p>' : '') + '</div></div>';
    if (d.type === 'relier') {
      const o = A().ordreDroite(d), lettre = k => Q.LETTRES_LONGUES[o.indexOf(k)];
      if (note) h += verdict(note.juste, note.juste ? 'Tout est bien relié.' : note.detail.filter(Boolean).length + ' paire' + (note.detail.filter(Boolean).length > 1 ? 's' : '') + ' bien reliée' + (note.detail.filter(Boolean).length > 1 ? 's' : '') + ' sur ' + d.paires.length + '.', '');
      h += '<ol class="relier-corr">' + d.paires.map((p, i) => {
        const ok = note ? note.detail[i] : null, choisi = r && r[i] >= 0 ? r[i] : null;
        return '<li class="' + (ok === true ? 'ok' : ok === false ? 'ko' : '') + '"><p><span class="r-num">' + (i + 1) + '</span> ' + t(p.gauche) + ' <span aria-hidden="true">→</span><span class="visuel-cache">va avec</span> <span class="r-num">' + lettre(i) + '</span> ' + t(p.droite)
          + (ok === false ? ' <span class="r-ta">(ta réponse : ' + (choisi === null ? 'aucune' : lettre(choisi)) + ')</span>' : '') + (ok === true ? ' <span class="r-ta">✓</span>' : '') + '</p>'
          + (p.feedback && (ok !== true || opts.tousOuverts) ? '<p class="r-fb">' + t(p.feedback) + '</p>' : '') + '</li>';
      }).join('') + '</ol>';
    } else if (d.type === 'puzzle') {
      if (note) {
        const k = note.detail.filter(Boolean).length;
        h += verdict(note.juste, note.juste ? 'Le programme est remis en ordre.' : k + ' ligne' + (k > 1 ? 's' : '') + ' sur ' + d.lignes.length + ' à leur place' + (A().avecIndent(d) ? ', avec la bonne indentation.' : '.'), '');
        if (!note.juste) {
          const tienne = r.map(([i, ind]) => ' '.repeat(4 * (A().avecIndent(d) ? ind : A().indentDe(d.lignes[i]))) + d.lignes[i].trim());
          const marques = {}; note.detail.forEach((ok, p) => { marques[p] = ok ? 'corrigee' : 'fautive'; });
          h += '<p class="fb-titre">Ta version (les lignes à revoir sont barrées)</p>' + Q.blocCode(tienne, { numeros: true, marques });
        }
      }
      h += '<p class="fb-titre">La solution</p>' + Q.blocCode(d.lignes, { numeros: true });
    } else if (d.type === 'ligne') {
      const bonne = d.ligne - 1, ok = note ? note.juste : null;
      if (note) h += verdict(ok, ok ? 'Bien vu : l\'erreur est à la ligne ' + d.ligne + '.' : 'Tu as choisi la ligne ' + (r + 1) + '. L\'erreur est à la ligne ' + d.ligne + '.',
        t(ok ? d.feedback : (d.pieges && d.pieges[String(r + 1)]) || d.feedback_autre));
      const marques = { [bonne]: 'fautive' }; if (note && !ok) marques[r] = 'choisie';
      h += Q.blocCode(d.code, { numeros: true, marques });
      h += '<p class="correction-ligne"><span>Ligne ' + d.ligne + ' corrigée</span> <code class="py">' + Q.colorerLigne(d.correction.trim()) + '</code></p>';
      if (!note || opts.tousOuverts) h += '<p>' + t(d.feedback) + '</p>';
    } else if (d.type === 'nuage') {
      if (d.exemples && d.exemples.length) h += '<p class="fb-titre">Des mots possibles</p><ul class="nuage-exemples">' + d.exemples.map(x => '<li>' + t(x) + '</li>').join('') + '</ul>';
    }
    if (d.explication) h += '<p class="explication"><span>À retenir</span> ' + t(d.explication) + '</p>';
    return h;
  };

  Q.rendreDiapo = function (cours, d, opts) {
    opts = opts || {};
    const total = cours.questions.length;
    if (d.type === 'titre') {
      return '<section class="diapo d-titre"><p class="surtitre">' + e(cours.niveau) + '</p><h1>' + t(d.titre || cours.titre) + '</h1>'
        + (cours.sous_titre ? '<p class="sous-titre">' + t(cours.sous_titre) + '</p>' : '')
        + (d.texte ? d.texte.map(p => '<p class="intro">' + t(p) + '</p>').join('') : '')
        + '<div class="colonnes"><div class="cadre"><h2>Critères de réussite</h2>' + liste(cours.criteres || []) + '</div>'
        + (d.conventions === false ? '' : '<div class="cadre"><h2>Conventions</h2>' + liste(cours.conventions || []) + '</div>') + '</div></section>';
    }
    if (d.type === 'partie') {
      return '<section class="diapo d-partie">' + (d.numero ? '<p class="p-num">' + e(d.numero) + '</p>' : '') + '<h2>' + t(d.titre) + '</h2>'
        + (d.sous_titre ? '<p class="sous-titre">' + t(d.sous_titre) + '</p>' : '') + '</section>';
    }
    if (d.type === 'classe') {
      // une question ouverte à la classe : pas de réponse à cocher ; les pistes apparaissent une à une
      return '<section class="diapo d-classe"><p class="surtitre">Question à la classe</p><h2 class="grande-question">' + t(d.question) + '</h2>'
        + (d.texte ? d.texte.map(p => '<p class="intro">' + t(p) + '</p>').join('') : '')
        + (d.pistes ? liste(d.pistes, 'pistes', true) : '') + (d.schema ? Q.schema(d.schema) : '') + (d.code ? code(d, d.code) : '') + '</section>';
    }
    if (d.type === 'humour') {
      return '<section class="diapo d-humour"><h2 class="grande-question">' + t(d.titre) + '</h2>' + liste(d.lignes || [], 'escalade', true)
        + (d.chute ? '<p class="chute frag">' + t(d.chute) + '</p>' : '') + '</section>';
    }
    if (d.type === 'notion') {
      return '<section class="diapo d-notion"><p class="surtitre">' + e(d.surtitre || 'Notion') + '</p><h2 class="d-titre-notion">' + t(d.titre) + '</h2><div class="n-corps"><div class="n-texte">' + liste(d.texte || [], 'puces', d.progressif === true)
        + (d.code ? code(d, d.code) : '') + (d.vocabulaire ? '<p class="vocab"><span>En anglais</span> ' + t(d.vocabulaire) + '</p>' : '') + consigne(d) + '</div>'
        + (d.schema ? Q.schema(d.schema) : '') + '</div>' + (d.chute ? '<p class="chute frag">' + t(d.chute) + '</p>' : '') + '</section>';
    }
    if (d.type === 'bilan') {
      const tb = d.tableau;
      return '<section class="diapo d-bilan"><h2 class="d-titre-notion">' + t(d.titre || 'À retenir') + '</h2>'
        + (tb ? '<div class="tableau"><table><thead><tr>' + tb.colonnes.map(c => '<th scope="col">' + t(c) + '</th>').join('') + '</tr></thead><tbody>' + tb.lignes.map(l => '<tr>' + l.map((c, i) => i ? '<td>' + t(c) + '</td>' : '<th scope="row">' + t(c) + '</th>').join('') + '</tr>').join('') + '</tbody></table></div>' : '')
        + (d.ticket ? '<div class="cadre ticket"><h3>Ticket de sortie</h3>' + liste(d.ticket) + '</div>' : '') + (opts.fin || '') + '</section>';
    }
    if (Q.INTERACTIFS.includes(d.type) && d.type !== 'question') return Q.rendreActivite(cours, d, opts);
    if (d.type === 'question') {
      return '<section class="diapo d-question" data-q="' + d.numero + '">' + Q.rendreEnonce(d, total)
        + '<div class="zone-options">' + Q.rendreOptions(d, { boutons: !!opts.boutons }) + '</div><div class="zone-correction" aria-live="polite"></div></section>';
    }
    return '';
  };
})(window);
