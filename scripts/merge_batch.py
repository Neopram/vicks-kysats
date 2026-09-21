# -*- coding: utf-8 -*-
"""Funde los lotes generados en el banco de la materia.

Los lotes llegan como JSON sueltos en STAGE/<spec>/*.json. Aqui se comprueban
uno a uno, se descartan los que no pasan, se reasignan los ids segun el tramo
reservado de cada seccion y se escribe el banco fundido en %TEMP%.
build.sh lo copia al repo despues.

Uso:  python merge_batch.py <spec A|B|C>
"""

import glob
import json
import os
import re
import sys

from vicks_common import CONTENT, OUT_DIR, SUBJECTS, write_out
from validate_bank import CITE_OK, MIN, PLACEHOLDER, dis_letters_ok, norm

STAGE = os.path.join(os.environ.get('TEMP', '/tmp'), 'vicks_stage')

# Tramo de ids reservado a cada seccion, para que los lotes en paralelo no choquen.
RANGES = {
    'A': {'path-cardio': (104, 233), 'path-resp': (234, 283), 'path-gi': (284, 413),
          'path-misc': (414, 803), 'path-neuro': (804, 1103)},
    'B': {'ped-neo': (104, 538), 'ped-resp': (539, 685),
          'ped-gi': (686, 812), 'ped-misc': (813, 1103)},
    'C': {'surg-acute': (117, 596), 'surg-trauma': (597, 776),
          'surg-misc': (777, 1116)},
}


def defects(q, spec, sections):
    """Motivos por los que una pregunta no entra. Vacio = entra."""
    bad = []
    for f, key in (('stem_el', 'stem'), ('stem_es', 'stem'),
                   ('expl_el', 'expl'), ('expl_es', 'expl'),
                   ('topic_el', 'topic'), ('topic_es', 'topic'),
                   ('dis_el', 'dis'), ('dis_es', 'dis')):
        v = (q.get(f) or '').strip()
        if len(v) < MIN[key]:
            bad.append('%s corto' % f)
        for pat, why in PLACEHOLDER:
            if re.search(pat, v, re.I | re.M):
                bad.append('%s: %s' % (f, why))
    if q.get('sid') not in sections:
        bad.append('sid %r ajeno a la materia' % q.get('sid'))
    opts = q.get('options') or []
    if len(opts) != 5:
        bad.append('%d opciones' % len(opts))
    seen = set()
    for j, o in enumerate(opts):
        for lang in ('el', 'es'):
            t = (o.get(lang) or '').strip()
            if len(t) < MIN['opt']:
                bad.append('opcion %s vacia' % chr(65 + j))
            for pat, why in PLACEHOLDER:
                if re.search(pat, t, re.I):
                    bad.append('opcion %s: %s' % (chr(65 + j), why))
        k = norm(o.get('es'))
        if k in seen:
            bad.append('opciones repetidas')
        seen.add(k)
    if not isinstance(q.get('correct'), int) or not 0 <= q['correct'] < max(1, len(opts)):
        bad.append('correct fuera de rango')
    if dis_letters_ok(q):
        bad.append('letras de dis_* desincronizadas con las opciones')
    cite = (q.get('cite') or '').strip()
    if len(cite) < MIN['cite'] or not CITE_OK.search(cite):
        bad.append('cita no verificable')
    if not isinstance(q.get('prob'), int) or not 50 <= q['prob'] <= 99:
        bad.append('prob fuera de 50-99')
    return bad


def main(spec):
    subj = SUBJECTS[spec]
    path = os.path.join(CONTENT, 'bank_%s.json' % spec)
    bank = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else []

    used_ids = {q['id'] for q in bank}
    stems = {norm(q.get('stem_es')): q['id'] for q in bank}
    by_sid = {}
    for q in bank:
        by_sid.setdefault(q['sid'], []).append(q)

    added = rejected = dupes = 0
    reasons = {}
    for f in sorted(glob.glob(os.path.join(STAGE, spec, '*.json'))):
        try:
            batch = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print('  %s ilegible: %s' % (os.path.basename(f), e))
            continue
        if isinstance(batch, dict):
            batch = batch.get('questions', [])
        for q in batch:
            bad = defects(q, spec, subj['sections'])
            if bad:
                rejected += 1
                for b in bad[:1]:
                    reasons[b] = reasons.get(b, 0) + 1
                continue
            k = norm(q.get('stem_es'))
            if k in stems:
                dupes += 1
                continue
            stems[k] = q.get('id', '?')
            by_sid.setdefault(q['sid'], []).append(q)
            added += 1

    # reasignar ids dentro del tramo de cada seccion
    out = []
    for sid, lo_hi in RANGES[spec].items():
        lo, hi = lo_hi
        qs = by_sid.get(sid, [])
        # las que ya tenian un id valido en el tramo lo conservan
        fixed = {}
        for q in qs:
            m = re.fullmatch(r'%s-(\d+)' % spec, q.get('id', ''))
            if m and lo <= int(m.group(1)) <= hi and int(m.group(1)) not in fixed:
                fixed[int(m.group(1))] = q
        free = (n for n in range(lo, hi + 1) if n not in fixed)
        for q in qs:
            if q not in fixed.values():
                try:
                    fixed[next(free)] = q
                except StopIteration:
                    print('  %s: tramo %d-%d lleno, sobran preguntas' % (sid, lo, hi))
                    break
        for n in sorted(fixed):
            fixed[n]['id'] = '%s-%d' % (spec, n)
            out.append(fixed[n])

    out.sort(key=lambda q: int(q['id'].split('-')[1]))
    dest = write_out('bank_%s.json' % spec, json.dumps(out, ensure_ascii=False, indent=1))

    print('%s: +%d nuevas, %d rechazadas, %d duplicadas -> %d en total'
          % (spec, added, rejected, dupes, len(out)))
    for r, n in sorted(reasons.items(), key=lambda x: -x[1])[:8]:
        print('   rechazo: %-40s %d' % (r, n))
    cnt = {}
    for q in out:
        cnt[q['sid']] = cnt.get(q['sid'], 0) + 1
    for sid, target in subj['sections'].items():
        print('   %-14s %4d / %4d' % (sid, cnt.get(sid, 0), target))
    print('   escrito en %s' % dest)


if __name__ == '__main__':
    for s in (sys.argv[1:] or ['A', 'B', 'C']):
        main(s)
