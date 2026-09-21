# -*- coding: utf-8 -*-
"""Puerta de calidad para los bancos de preguntas v6.

Existe porque el validador anterior solo miraba el esquema: comprobaba que
hubiera una .q-cite, no que la cita fuera real; que data-correct estuviera
entre 0 y 4, no que no fuera siempre 0. Asi se colaron 698 tarjetas plantilla
marcadas como "Revisada" al 86 %.

Uso:  python validate_bank.py <spec A|B|C> [--strict]
Codigo de salida 1 si hay errores.
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from vicks_common import CONTENT, SUBJECTS

# --------------------------------------------------------------- plantillas --
# Patrones que delatan contenido generado sin pensar. Cualquiera invalida.
PLACEHOLDER = [
    (r'\bPregunta sobre\b', 'enunciado plantilla "Pregunta sobre X"'),
    (r'\bΕρωτηση σχετικα\b', 'enunciado plantilla en griego'),
    (r'\bIncorrecto\s*\d', 'distractor plantilla "Incorrecto N"'),
    (r'\bΛαθος\s*\d', 'distractor plantilla "Λαθος N"'),
    (r'Respuesta correcta', 'la opcion se autodelata como correcta'),
    (r'Σωστη απαντηση', 'la opcion se autodelata como correcta (el)'),
    (r'\bExplicacion sobre\b', 'explicacion plantilla'),
    (r'\bΕξηγηση για\b', 'explicacion plantilla (el)'),
    (r'^(Expl|Εξηγ|Ref|Λ|L)$', 'campo de relleno de una palabra'),
    (r'\bTopic-\d|\bSurgery-\d|\btopic_\d', 'tema autogenerado sin contenido'),
]

# Una cita creible lleva año, edicion, o el nombre de una fuente reconocible.
CITE_OK = re.compile(
    r'(1[89]\d\d|20\d\d)'
    r'|\d+\s*(\.\s*)?(ª|a|th|nd|rd|st)\s*(ed|έκδ)'
    r'|\b(Harrison|Davidson|Nelson|Sabiston|Schwartz|Cecil|ATLS|NRP|UpToDate'
    r'|ESC|AHA|ACC|IDSA|KDIGO|GOLD|GINA|ADA|EASL|ACG|ACR|EULAR|WHO|NICE|AAP'
    r'|ISPAD|ESPGHAN|ASH|NCCN|Tintinalli|Robbins|Guyton|Williams)\b',
    re.I)

MIN = {'stem': 40, 'expl': 40, 'dis': 30, 'cite': 12, 'topic': 4, 'opt': 2}


def norm(s):
    """Minusculas sin acentos ni puntuacion, para comparar duplicados."""
    s = unicodedata.normalize('NFD', (s or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9α-ω ]+', ' ', s).strip()


def dis_letters_ok(q):
    """Las letras citadas en dis_* deben ser exactamente las opciones incorrectas.

    Un agente reordeno opciones para romper el sesgo de posicion y dejo el
    analisis de distractores apuntando a las letras viejas: la pregunta explica
    por que falla la opcion correcta y calla una de las incorrectas.
    """
    n = len(q.get('options') or [])
    cor = q.get('correct')
    if not isinstance(cor, int) or not 0 <= cor < n:
        return []
    expect = {chr(65 + i) for i in range(n)} - {chr(65 + cor)}
    bad = []
    for f in ('dis_es', 'dis_el'):
        got = set(re.findall(r'<b>([A-E])</b>', q.get(f) or ''))
        if got and got != expect:
            bad.append('%s cita %s y deberia citar %s'
                       % (f, ''.join(sorted(got)) or '-', ''.join(sorted(expect))))
    return bad


def check_placeholder(text, where, errs, qid):
    for pat, why in PLACEHOLDER:
        if re.search(pat, text or '', re.I | re.M):
            errs.append('%s %s: %s' % (qid, where, why))
            return True
    return False


def validate(spec, strict=False):
    subj = SUBJECTS[spec]
    path = os.path.join(CONTENT, 'bank_%s.json' % spec)
    if not os.path.exists(path):
        print('%s: no hay banco todavia (%s)' % (spec, path))
        return 0
    bank = json.load(open(path, encoding='utf-8'))

    errs, warns = [], []
    seen_ids, seen_stems = {}, {}
    pos_by_sid = defaultdict(Counter)

    # ids que ya usa la app raiz y no se pueden reutilizar
    reserved = {'A': 103, 'B': 103, 'C': 116}[spec]

    for i, q in enumerate(bank):
        qid = q.get('id', '#%d' % i)

        # --- identidad -----------------------------------------------------
        m = re.fullmatch(r'([ABC])-(\d+)', qid)
        if not m:
            errs.append('%s id con formato invalido' % qid)
            continue
        if m.group(1) != spec:
            errs.append('%s prefijo no corresponde a la materia %s' % (qid, spec))
        n = int(m.group(2))
        if n <= reserved:
            errs.append('%s reutiliza un id de la app raiz (<=%d)' % (qid, reserved))
        if qid in seen_ids:
            errs.append('%s id duplicado (ya en la posicion %d)' % (qid, seen_ids[qid]))
        seen_ids[qid] = i

        if q.get('sid') not in subj['sections']:
            errs.append('%s sid "%s" no pertenece a %s' % (qid, q.get('sid'), spec))

        # --- contenido bilingue --------------------------------------------
        for field, key in (('stem_el', 'stem'), ('stem_es', 'stem'),
                           ('expl_el', 'expl'), ('expl_es', 'expl'),
                           ('topic_el', 'topic'), ('topic_es', 'topic')):
            val = (q.get(field) or '').strip()
            if len(val) < MIN[key]:
                errs.append('%s %s demasiado corto (%d < %d car.)'
                            % (qid, field, len(val), MIN[key]))
            check_placeholder(val, field, errs, qid)

        for field in ('dis_el', 'dis_es'):
            val = (q.get(field) or '').strip()
            if len(val) < MIN['dis']:
                warns.append('%s %s ausente o muy corto: sin analisis de distractores'
                             % (qid, field))
            check_placeholder(val, field, errs, qid)

        # --- opciones -------------------------------------------------------
        opts = q.get('options') or []
        if len(opts) != 5:
            errs.append('%s tiene %d opciones (deben ser 5)' % (qid, len(opts)))
        texts_es, texts_el = [], []
        for j, o in enumerate(opts):
            for lang, bucket in (('el', texts_el), ('es', texts_es)):
                t = (o.get(lang) or '').strip()
                if len(t) < MIN['opt']:
                    errs.append('%s opcion %s vacia en %s' % (qid, chr(65 + j), lang))
                check_placeholder(t, 'opcion %s (%s)' % (chr(65 + j), lang), errs, qid)
                bucket.append(norm(t))
        for bucket, lang in ((texts_es, 'es'), (texts_el, 'el')):
            dup = [t for t, c in Counter(bucket).items() if c > 1 and t]
            if dup:
                errs.append('%s opciones repetidas en %s' % (qid, lang))

        cor = q.get('correct')
        if not isinstance(cor, int) or not 0 <= cor < max(1, len(opts)):
            errs.append('%s correct=%r fuera de rango' % (qid, cor))
        else:
            pos_by_sid[q.get('sid')][cor] += 1

        for b in dis_letters_ok(q):
            errs.append('%s %s' % (qid, b))

        # --- cita -----------------------------------------------------------
        cite = (q.get('cite') or '').strip()
        if len(cite) < MIN['cite']:
            errs.append('%s sin cita utilizable ("%s")' % (qid, cite))
        elif not CITE_OK.search(cite):
            errs.append('%s cita no verificable, falta año/edicion/fuente: "%s"'
                        % (qid, cite[:60]))

        # --- probabilidad ----------------------------------------------------
        prob = q.get('prob')
        if not isinstance(prob, int) or not 50 <= prob <= 99:
            errs.append('%s prob=%r fuera de 50-99' % (qid, prob))

        # --- duplicados de enunciado -----------------------------------------
        key = norm(q.get('stem_es'))
        if key and key in seen_stems:
            errs.append('%s enunciado duplicado de %s' % (qid, seen_stems[key]))
        seen_stems[key] = qid

    # --- sesgo de posicion de la respuesta correcta --------------------------
    for sid, c in pos_by_sid.items():
        total = sum(c.values())
        if total < 20:
            continue
        for pos, cnt in c.items():
            if cnt / total > 0.35:
                errs.append('%s: la correcta cae en la posicion %s en el %d %% de las '
                            'preguntas (max 35 %%)' % (sid, chr(65 + pos), cnt * 100 / total))

    # --- cobertura por seccion ------------------------------------------------
    by_sid = Counter(q.get('sid') for q in bank)
    print('--- %s (%s) : %d preguntas ---' % (subj['dir'], spec, len(bank)))
    for sid, target in subj['sections'].items():
        have = by_sid.get(sid, 0)
        flag = 'OK ' if have >= target else '   '
        print('  %s %-14s %4d / %4d  (%d %%)'
              % (flag, sid, have, target, have * 100 // max(1, target)))

    for w in warns[:15]:
        print('  aviso: %s' % w)
    if len(warns) > 15:
        print('  aviso: ... y %d mas' % (len(warns) - 15))
    for e in errs[:40]:
        print('  ERROR: %s' % e)
    if len(errs) > 40:
        print('  ERROR: ... y %d mas' % (len(errs) - 40))

    if errs:
        print('  => %d ERRORES. El banco no pasa.' % len(errs))
    else:
        print('  => sin errores%s' % (' (%d avisos)' % len(warns) if warns else ''))
    return len(errs)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    strict = '--strict' in sys.argv
    total = sum(validate(s, strict) for s in (args or ['A', 'B', 'C']))
    sys.exit(1 if total else 0)
