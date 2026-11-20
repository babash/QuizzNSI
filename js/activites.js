/* QuizzNSI : les autres types de questions (MIT, Babash - NSI Tani Malandi).
   - « nuage » : chaque élève propose autant de mots qu'il ou elle veut (un ou deux mots à chaque fois) et vote
     pour les mots de ses camarades ; la page projetée affiche le nuage ; non noté ;
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

  /* Le nuage de la classe, tenu par la page projetée (fonctions pures, l'état est un objet simple) :
     { suivant, mots: [{ k, m, cle, de: [identifiants], votes: [identifiants] }], supprimes: [empreintes] }.
     - proposer : autant de mots qu'on veut ; un mot déjà proposé (même clé : sans casse, sans accents, sosies
       compris) ajoute une voix au lieu d'un doublon ; un mot supprimé ne revient pas ;
     - voter : une voix par élève et par mot, jamais pour un mot qu'on a soi-même proposé ;
     - supprimer : le mot disparaît (et ses voix) ; seule son empreinte (un nombre) reste, pour le refuser ensuite ;
     - affiches : les mots montrés, avec leur nombre de voix (élèves qui l'ont proposé ou qui ont voté pour). */
  const PAR_ELEVE_MAX = 100, AFFICHES_MAX = 200;
  const nuageVide = () => ({ suivant: 0, mots: [], supprimes: [] });
  const voix = w => new Set(w.de.concat(w.votes)).size;
  function proposer(n, id, brut) {
    const f = filtrerMot(brut); if (!f.ok) return 'refuse';
    const cle = Q.clePseudo ? Q.clePseudo(f.mot) : f.mot;
    if (!cle || n.supprimes.includes(Q.graine(cle))) return 'supprime';
    if (n.mots.filter(w => w.de.includes(id)).length >= PAR_ELEVE_MAX) return 'refuse';
    const w = n.mots.find(x => x.cle === cle);
    if (w) { if (!w.de.includes(id)) { w.de.push(id); w.votes = w.votes.filter(x => x !== id); } return 'voix'; }
    n.mots.push({ k: n.suivant++, m: f.mot, cle, de: [id], votes: [] });
    return 'ajoute';
  }
  function voter(n, id, k) {
    const w = n.mots.find(x => x.k === k);
    if (!w || w.de.includes(id) || w.votes.includes(id)) return false;
    w.votes.push(id); return true;
  }
  function supprimer(n, k) {
    const i = n.mots.findIndex(x => x.k === k); if (i < 0) return false;
    n.supprimes.push(Q.graine(n.mots[i].cle)); n.mots.splice(i, 1); return true;
  }
  function affiches(n, seuil) {
    return n.mots.map(w => ({ k: w.k, m: w.m, n: voix(w) })).filter(w => w.n >= (seuil || 1))
      .sort((a, b) => b.n - a.n || a.k - b.k).slice(0, AFFICHES_MAX);
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
    if (d.type === 'nuage') {
      // un mot proposé, ou une voix pour le mot numéro k : { vote: k }
      if (r !== null && typeof r === 'object' && !Array.isArray(r)) return Object.keys(r).length === 1 && entier(r.vote, 0, 99999) ? { vote: r.vote } : null;
      const f = filtrerMot(r); return f.ok ? f.mot : null;
    }
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

  Q.activites = { MOT_MAX, RELIER_MAX, PUZZLE_MAX, INDENT_MAX, PAR_ELEVE_MAX, AFFICHES_MAX, filtrerMot, nuageVide, proposer, voter, supprimer, affiches, voix, ordreDroite, ordrePuzzle, indentDe, avecIndent, valider, noter, controler, brut, NOMS };
  if (typeof module !== 'undefined' && module.exports) module.exports = Q.activites;
})(typeof window !== 'undefined' ? window : globalThis);
