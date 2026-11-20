/* QuizzNSI : la version à imprimer (MIT, Babash - NSI Tani Malandi).
   imprimer.html?cours=<id> : le sujet (les 20 questions) ; &corrige : le corrigé, à part. */
(function () {
  'use strict';
  const Q = window.QuizzNSI, $ = Q.$, t = Q.texte, e = Q.echapper;
  const params = new URLSearchParams(location.search), corrige = params.has('corrige');

  function entete(cours, titre) {
    return '<header class="f-entete"><div><p class="f-niveau">' + e(cours.niveau) + ' · ' + e(titre) + '</p><h1>' + t(cours.titre) + '</h1></div>'
      + (corrige ? '' : '<div class="f-champs"><p>Prénom : ……………………………</p><p>Classe : ………… Date : …………</p></div>') + '</header>';
  }
  const pied = cours => '<p class="f-pied">' + e(cours.auteur) + ' · ' + e(cours.licence) + ' · QuizzNSI</p>';

  // Les autres types de questions, sur papier : la consigne, les éléments, et la place pour répondre.
  const autres = cours => cours.interactifs.filter(d => d.type !== 'question');
  const titreAutre = d => '<h2><span class="f-num">' + e(Q.activites.NOMS[d.type]) + ' ·</span> ' + t(d.nom) + '</h2><p class="f-objectif">Objectif : ' + t(d.objectif) + '</p>';
  function sujetAutre(d) {
    let h = '<section class="f-question f-activite">' + titreAutre(d) + d.enonce.map(p => '<p>' + t(p) + '</p>').join('') + (d.code && d.type !== 'ligne' ? Q.blocCode(d.code) : '');
    if (d.type === 'nuage') h += '<p class="f-ligne">Un ou deux mots : ……………………………………</p>';
    if (d.type === 'relier') h += '<p class="f-consigne">Relier chaque élément de gauche à une seule réponse : écrire la lettre après la flèche.</p>' + Q.rendreElements(d, { papier: true });
    if (d.type === 'puzzle') h += Q.rendreElements(d) + '<p class="f-consigne">Écrire les lettres dans l\'ordre du programme' + (Q.activites.avecIndent(d) ? ', puis recopier le programme avec son indentation' : '') + ' :</p><p class="f-ligne">Ordre : ' + d.lignes.map(() => '……').join(' ') + '</p>' + (Q.activites.avecIndent(d) ? '<div class="f-cadre-code" aria-hidden="true"></div>' : '');
    if (d.type === 'ligne') h += Q.rendreElements(d) + '<p class="f-ligne">Ligne fautive : …… Correction : ……………………………………………</p>';
    return h + '</section>';
  }
  function corrigeAutre(d) {
    return '<section class="f-question f-corr f-activite">' + titreAutre(d) + Q.rendreCorrectionActivite(d, null, { tousOuverts: true }) + '</section>';
  }

  function sujet(cours) {
    const n = autres(cours).length;
    let h = entete(cours, 'cours-quiz, ' + cours.questions.length + ' questions' + (n ? ' et ' + n + ' activité' + (n > 1 ? 's' : '') : ''));
    h += '<div class="f-consignes"><p><strong>Consigne :</strong> pour chaque question, cocher la seule bonne réponse.</p>'
      + '<p><strong>Conventions</strong></p><ul>' + (cours.conventions || []).map(c => '<li>' + t(c) + '</li>').join('') + '</ul></div>';
    h += cours.interactifs.map(q => q.type !== 'question' ? sujetAutre(q) : '<section class="f-question"><h2><span class="f-num">' + q.numero + '.</span> ' + t(q.nom) + '</h2>'
      + '<p class="f-objectif">Objectif : ' + t(q.objectif) + '</p>'
      + q.enonce.map(p => '<p>' + t(p) + '</p>').join('')
      + (q.code || q.schema ? '<div class="f-illus">' + (q.code ? Q.blocCode(q.code) : '') + (q.schema ? Q.schema(q.schema) : '') + '</div>' : '')
      + '<ol class="f-options">' + q.options.map((o, i) => '<li><span class="case" aria-hidden="true"></span>' + Q.pastille(i) + '<span>' + (o.texte ? t(o.texte) : '') + (o.code ? Q.blocCode(o.code, { numeros: false }) : '') + '</span></li>').join('') + '</ol></section>').join('');
    return h + pied(cours);
  }

  function correction(cours) {
    let h = entete(cours, 'corrigé');
    h += '<table class="f-grille"><caption>Les bonnes réponses</caption><tr><th scope="row">Question</th>' + cours.questions.map(q => '<td>' + q.numero + '</td>').join('') + '</tr>'
      + '<tr><th scope="row">Réponse</th>' + cours.questions.map(q => '<td><strong>' + Q.LETTRES[q.bonne] + '</strong></td>').join('') + '</tr></table>';
    h += cours.interactifs.map(q => {
      if (q.type !== 'question') return corrigeAutre(q);
      const b = q.options[q.bonne];
      return '<section class="f-question f-corr"><h2><span class="f-num">' + q.numero + '.</span> ' + t(q.nom) + ' : <strong>' + Q.LETTRES[q.bonne] + '</strong></h2>'
        + '<p>' + Q.pastille(q.bonne) + ' ' + (b.texte ? t(b.texte) : '') + '</p>' + (b.code ? Q.blocCode(b.code, { numeros: false }) : '')
        + '<p><strong>À retenir :</strong> ' + t(q.explication) + '</p><p>' + t(b.feedback) + '</p>'
        + '<ul class="f-pieges">' + q.options.map((o, i) => i === q.bonne ? '' : '<li><strong>' + Q.LETTRES[i] + '</strong> : ' + t(o.feedback) + '</li>').join('') + '</ul>'
        + Q.rendreTrace(q.trace) + '</section>';
    }).join('');
    const bilan = cours.diapositives.find(d => d.type === 'bilan');
    if (bilan && bilan.tableau) {
      h += '<section class="f-question"><h2>' + t(bilan.titre || 'À retenir') + '</h2><table class="f-tableau"><thead><tr>' + bilan.tableau.colonnes.map(c => '<th>' + t(c) + '</th>').join('') + '</tr></thead><tbody>'
        + bilan.tableau.lignes.map(l => '<tr>' + l.map((c, i) => i ? '<td>' + t(c) + '</td>' : '<th scope="row">' + t(c) + '</th>').join('') + '</tr>').join('') + '</tbody></table></section>';
    }
    return h + pied(cours);
  }

  async function demarrer() {
    Q.theme();
    let cours;
    try { cours = await Q.chargerCours(Q.idCours()); }
    catch (err) { Q.erreurPage($('feuille'), err.message); return; }
    document.title = 'QuizzNSI · ' + cours.titre + (corrige ? ' · corrigé' : ' · questions à imprimer');
    $('titreCours').textContent = cours.titre + (corrige ? ' · corrigé' : ' · questions à imprimer');
    const autre = new URL(location.href);
    if (corrige) autre.searchParams.delete('corrige'); else autre.searchParams.set('corrige', '');
    $('basculer').href = autre.pathname + autre.search.replace('corrige=', 'corrige');
    $('basculer').textContent = corrige ? 'Les questions' : 'Le corrigé';
    $('feuille').innerHTML = corrige ? correction(cours) : sujet(cours);
    $('imprimer').addEventListener('click', () => window.print());
  }
  demarrer();
})();
