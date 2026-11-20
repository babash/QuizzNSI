/* QuizzNSI : les autres types de questions (MIT, Babash - NSI Tani Malandi).
   - « nuage » : chaque élève envoie un mot ou deux, la page projetée affiche le nuage ; non noté ;
   - « relier » : associer deux à deux (terme et définition, code et sortie) ;
   - « puzzle » : remettre des lignes de code dans l'ordre, et à la bonne indentation ;
   - « ligne » : toucher la ligne qui contient l'erreur.
   Ce fichier ne contient que des fonctions pures (aucune page, aucun réseau), testées par tests/test_moteur.js :
   le contrôle d'un mot du nuage, le contrôle d'une réponse, la note d'une réponse, l'ordre d'affichage.
   Une réponse reçue n'est jamais affichée telle quelle : elle est d'abord contrôlée ici, contre la diapositive
   du fichier du cours (longueurs, indices, permutation). */
(function (racine) {
  'use strict';
  const Q = racine.QuizzNSI = racine.QuizzNSI || {};

  const MOT_MAX = 24;          // caractères pour un mot du nuage (un mot ou deux)
  const RELIER_MAX = 6, PUZZLE_MAX = 12, INDENT_MAX = 6, LIGNES_MAX = 40;
  const entier = (v, a, b) => Number.isSafeInteger(v) && v >= a && v <= b;

  /* ── Nuage de mots ────────────────────────── */
  // Un mot ou deux : 2 à 24 caractères ; lettres de toutes les écritures (une seule par mot envoyé), chiffres,
  // espace, tiret, apostrophe. Aucun caractère invisible ou de contrôle, aucune balise, aucun lien possible.
  function filtrerMot(brut) {
    if (typeof brut !== 'string' || brut.length > 200) return { ok: false, raison: 'Écris un mot ou deux.' };
    if (/[\p{C}\p{Zl}\p{Zp}]/u.test(brut)) return { ok: false, raison: 'Ce mot contient un caractère invisible : écris-le de nouveau, au clavier.' };
    const m = brut.normalize('NFC').replace(/\s+/gu, ' ').trim();
    const n = [...m].length;
    if (n < 2) return { ok: false, raison: 'Deux caractères au moins.' };
    if (n > MOT_MAX) return { ok: false, raison: MOT_MAX + ' caractères au plus.' };
    if (m.split(' ').length > 2) return { ok: false, raison: 'Un mot ou deux, pas plus.' };
    if (!/^[\p{L}\p{M}\p{Nd}][\p{L}\p{M}\p{Nd} '’-]*$/u.test(m)) return { ok: false, raison: 'Seulement des lettres, des chiffres, une espace, - et \'.' };
    if (Q.ecritures && Q.ecritures(m).size > 1) return { ok: false, raison: 'Écris le mot dans une seule écriture.' };
    return { ok: true, mot: m.toLocaleLowerCase('fr') };
  }

  /* Le nuage : les mots regroupés (sans casse, sans accents, sosies compris), sans les mots masqués par
     l'enseignant·e, avec le seuil choisi (1 : tous les mots ; 2 : les mots donnés par 2 élèves au moins).
     Renvoie [{ cle, mot, n }] trié par nombre décroissant puis par ordre alphabétique. */
  function nuage(mots, masques, seuil) {
    const g = new Map(), m = new Set(masques || []);
    for (const brut of mots) {
      const f = filtrerMot(brut); if (!f.ok) continue;
      const cle = Q.clePseudo ? Q.clePseudo(f.mot) : f.mot;
      if (!cle || m.has(cle)) continue;
      const e = g.get(cle) || { cle, mot: f.mot, n: 0 }; e.n++; g.set(cle, e);
    }
    return [...g.values()].filter(e => e.n >= (seuil || 1)).sort((a, b) => b.n - a.n || a.mot.localeCompare(b.mot, 'fr'));
  }

  /* ── L'ordre d'affichage, le même sur tous les appareils ── */
  // Il dépend de l'identifiant de la diapositive (ou d'une graine donnée, pour rejouer) : la page projetée et
  // les téléphones voient le même ordre, et on peut dire « 1 avec C » à toute la classe.
  const graineDe = d => (Number.isSafeInteger(d.graine) ? d.graine : Q.graine(d.id)) >>> 0;
  function ordreDroite(d) { return Q.melanger(d.paires.map((_, i) => i), graineDe(d)); }
  function ordrePuzzle(d) {
    const n = d.lignes.length, id = Array.from({ length: n }, (_, i) => i);
    let o = Q.melanger(id, graineDe(d));
    // jamais l'ordre de la solution, ni des lignes identiques dans le même ordre
    const texte = o.map(i => d.lignes[i].trim()).join('\n');
    if (texte === d.lignes.map(l => l.trim()).join('\n')) o = o.slice(1).concat(o[0]);
    return o;
  }
  const indentDe = ligne => Math.floor(((ligne.match(/^ */) || [''])[0].length) / 4);
  const avecIndent = d => d.indentation !== false;

  /* ── Contrôle d'une réponse, contre la diapositive du cours ──
     Renvoie la réponse normalisée, ou null si elle n'est pas conforme. */
  function valider(d, r) {
    if (!d) return null;
    if (d.type === 'nuage') { const f = filtrerMot(r); return f.ok ? f.mot : null; }
    if (d.type === 'ligne') return entier(r, 0, d.code.length - 1) ? r : null;
    if (d.type === 'relier') {
      const n = d.paires.length;
      if (!Array.isArray(r) || r.length !== n || !r.every(x => entier(x, -1, n - 1))) return null;
      const vus = r.filter(x => x >= 0);
      return new Set(vus).size === vus.length ? r.slice() : null;
    }
    if (d.type === 'puzzle') {
      const n = d.lignes.length;
      if (!Array.isArray(r) || r.length !== n) return null;
      if (!r.every(x => Array.isArray(x) && x.length === 2 && entier(x[0], 0, n - 1) && entier(x[1], 0, INDENT_MAX))) return null;
      if (new Set(r.map(x => x[0])).size !== n) return null;
      return r.map(x => [x[0], x[1]]);
    }
    return null;
  }

  /* ── La note d'une réponse ──
     { juste, part, detail } : part (de 0 à 1) est la part de la réponse qui est juste.
     - relier : chaque paire bien reliée compte (3 paires sur 4 : part 0,75) ;
     - puzzle : chaque ligne à sa place, et à la bonne indentation quand elle compte ;
     - ligne : juste ou faux ;
     - nuage : non noté (null). */
  function noter(d, r) {
    const v = valider(d, r);
    if (d.type === 'nuage') return null;
    if (v === null) return { juste: false, part: 0, detail: [] };
    if (d.type === 'ligne') { const j = v === d.ligne - 1; return { juste: j, part: j ? 1 : 0, detail: [j] }; }
    if (d.type === 'relier') { const det = v.map((x, i) => x === i); const k = det.filter(Boolean).length; return { juste: k === det.length, part: k / det.length, detail: det }; }
    if (d.type === 'puzzle') {
      const sol = d.lignes;
      const det = v.map(([i, ind], p) => sol[i].trim() === sol[p].trim() && (!avecIndent(d) || ind === indentDe(sol[p])));
      const k = det.filter(Boolean).length;
      return { juste: k === det.length, part: k / det.length, detail: det };
    }
    return null;
  }

  /* Contrôle léger de la forme d'une diapositive (dans le navigateur) ; le contrôle complet est outils/verifier_cours.py. */
  function controler(d) {
    const chaines = v => Array.isArray(v) && v.every(x => typeof x === 'string');
    if (!/^[a-z0-9-]{1,20}$/.test(String(d.id))) return 'identifiant invalide';
    if (d.type === 'nuage') return null;
    if (d.type === 'relier') return Array.isArray(d.paires) && d.paires.length >= 2 && d.paires.length <= RELIER_MAX && d.paires.every(p => p && typeof p.gauche === 'string' && typeof p.droite === 'string') ? null : 'relier : 2 à ' + RELIER_MAX + ' paires { gauche, droite }';
    if (d.type === 'puzzle') return chaines(d.lignes) && d.lignes.length >= 3 && d.lignes.length <= PUZZLE_MAX ? null : 'puzzle : 3 à ' + PUZZLE_MAX + ' lignes';
    if (d.type === 'ligne') return chaines(d.code) && d.code.length >= 2 && d.code.length <= LIGNES_MAX && entier(d.ligne, 1, d.code.length) ? null : 'ligne : du code et le numéro de la ligne fautive';
    return 'type inconnu';
  }

  // Le texte brut d'un texte du cours (pour une liste déroulante ou un aria-label) : sans `, ==, **.
  const brut = t => String(t == null ? '' : t).replace(/`/g, '').replace(/==|\*\*/g, '').replace(/\*/g, '');
  const NOMS = { question: 'Question', nuage: 'Nuage de mots', relier: 'Relier', puzzle: 'Puzzle de code', ligne: 'Trouver la ligne fautive' };

  Q.activites = { MOT_MAX, RELIER_MAX, PUZZLE_MAX, INDENT_MAX, filtrerMot, nuage, ordreDroite, ordrePuzzle, indentDe, avecIndent, valider, noter, controler, brut, NOMS };
  if (typeof module !== 'undefined' && module.exports) module.exports = Q.activites;
})(typeof window !== 'undefined' ? window : globalThis);
