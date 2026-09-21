# -*- coding: utf-8 -*-
"""Reparte la respuesta correcta entre las cinco posiciones.

Los modelos tienden a dejar la correcta en A. Permutar las opciones sin mas
rompe el analisis de distractores, porque dis_el/dis_es citan letras: aqui se
permuta y se reetiquetan las letras en el mismo paso, de modo que <b>C</b>
sigue senalando al mismo texto que antes.

Es determinista: el mismo banco produce siempre el mismo reparto, asi que
recompilar no altera las preguntas ya estudiadas.

Uso:  python rebalance.py <spec A|B|C>   -> reescribe %TEMP%/vicks_build/bank_<spec>.json
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

from vicks_common import CONTENT, SUBJECTS, write_out


def rng(seed_text):
    h = int(hashlib.sha1(seed_text.encode('utf-8')).hexdigest()[:8], 16)

    def nxt(n):
        nonlocal h
        h = (h * 1103515245 + 12345) & 0x7FFFFFFF
        return h % n
    return nxt


def permute(q, target):
    """Mueve la opcion correcta a `target` y baraja el resto. Devuelve True si cambio."""
    n = len(q['options'])
    cor = q['correct']
    if cor == target:
        return False

    others = [i for i in range(n) if i != cor]
    nxt = rng(q.get('id', '') + q.get('stem_es', '')[:60])
    for i in range(len(others) - 1, 0, -1):
        j = nxt(i + 1)
        others[i], others[j] = others[j], others[i]

    # order[j] = indice viejo que pasa a ocupar la posicion j
    order = [None] * n
    order[target] = cor
    it = iter(others)
    for j in range(n):
        if order[j] is None:
            order[j] = next(it)

    q['options'] = [q['options'][order[j]] for j in range(n)]
    q['correct'] = target

    # old -> new, para reescribir las letras del analisis de distractores
    new_of = {old: new for new, old in enumerate(order)}
    for f in ('dis_el', 'dis_es'):
        if not q.get(f):
            continue
        q[f] = re.sub(
            r'<b>([A-E])</b>',
            lambda m: '<b>%s</b>' % chr(65 + new_of[ord(m.group(1)) - 65]),
            q[f])
    return True


def main(spec):
    src = os.path.join(os.environ.get('TEMP', '/tmp'), 'vicks_build',
                       'bank_%s.json' % spec)
    if not os.path.exists(src):
        src = os.path.join(CONTENT, 'bank_%s.json' % spec)
    if not os.path.exists(src):
        print('%s: no hay banco' % spec)
        return
    bank = json.load(open(src, encoding='utf-8'))

    by_sid = defaultdict(list)
    for q in bank:
        by_sid[q['sid']].append(q)

    moved = 0
    for sid, qs in by_sid.items():
        n = len(qs[0]['options']) if qs else 5
        # posiciones objetivo repartidas por igual, en orden estable
        qs_sorted = sorted(qs, key=lambda q: q.get('id', ''))
        for k, q in enumerate(qs_sorted):
            if permute(q, k % n):
                moved += 1

    dest = write_out('bank_%s.json' % spec,
                     json.dumps(bank, ensure_ascii=False, indent=1))
    print('%s: %d de %d preguntas reordenadas' % (spec, moved, len(bank)))
    for sid in sorted(by_sid):
        c = Counter(q['correct'] for q in by_sid[sid])
        tot = sum(c.values())
        print('   %-14s %s' % (sid, '  '.join(
            '%s=%d%%' % (chr(65 + p), c.get(p, 0) * 100 // tot) for p in range(5))))
    print('   escrito en %s' % dest)


if __name__ == '__main__':
    for s in (sys.argv[1:] or ['A', 'B', 'C']):
        main(s)
