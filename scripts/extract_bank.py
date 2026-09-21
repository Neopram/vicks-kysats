# -*- coding: utf-8 -*-
"""Rescata las preguntas REALES de un index.html v6 y las vuelca a JSON.

Descarta las tarjetas plantilla ("Pregunta sobre X" / "Incorrecto 1") y
rebaraja las opciones de forma determinista, porque el generador viejo dejo
la respuesta correcta en la posicion A en las 1000 tarjetas.

Uso:  python extract_bank.py <index.html> <spec A|B|C>  ->  OUT_DIR/bank_<spec>.json
"""

import hashlib
import json
import re
import sys

from vicks_common import write_out

PLACEHOLDER = re.compile(r'Pregunta sobre |Incorrecto 1<|Ερωτηση σχετικα με ')


def grab(pat, text, default=''):
    m = re.search(pat, text, re.S)
    return m.group(1).strip() if m else default


def parse_cards(html):
    """Trocea el HTML en (sid, bloque de tarjeta)."""
    out = []
    sid = None
    for chunk in re.split(r'(?=<section id="|<div class="card")', html):
        m = re.match(r'<section id="([a-z-]+)"', chunk)
        if m:
            sid = m.group(1)
            continue
        if chunk.startswith('<div class="card') and sid:
            out.append((sid, chunk))
    return out


def shuffled_order(qid, n):
    """Permutacion determinista a partir del id, para romper el sesgo de posicion."""
    seed = int(hashlib.sha1(qid.encode()).hexdigest()[:8], 16)
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        j = seed % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def main(path, spec):
    html = open(path, encoding='utf-8').read()
    bank, skipped = [], 0

    for sid, card in parse_cards(html):
        if 'q-options' not in card:
            continue
        qid = grab(r'class="card-number">([^<]+)<', card)
        if not qid:
            continue
        if PLACEHOLDER.search(card):
            skipped += 1
            continue

        ul = grab(r'<ul class="q-options"[^>]*>(.*?)</ul>', card)
        correct = int(grab(r'<ul class="q-options" data-correct="(\d+)"', card, '0'))
        opts = []
        for li in re.findall(r'<li[^>]*>(.*?)</li>', ul, re.S):
            opts.append({
                'el': grab(r'<span class="lang-el">(.*?)</span>', li),
                'es': grab(r'<span class="lang-es">(.*?)</span>', li),
            })
        if len(opts) < 4:
            skipped += 1
            continue

        # rebarajar para que la correcta no caiga siempre en A
        order = shuffled_order(qid, len(opts))
        opts = [opts[i] for i in order]
        correct = order.index(correct)

        expl = grab(r'<div class="q-explanation"[^>]*>(.*?)<div class="q-dis"', card) \
            or grab(r'<div class="q-explanation"[^>]*>(.*?)</div>', card)
        dis = grab(r'<div class="q-dis">(.*?)</div>', card)

        bank.append({
            'id': qid,
            'sid': sid,
            'concepts': [c for c in grab(r'data-concepts="([^"]*)"', card).split(',') if c],
            'prob': int(grab(r'class="prob[^"]*">(\d+)%', card, '80')),
            'topic_el': grab(r'<div class="card-greek">(.*?)</div>', card),
            'topic_es': grab(r'<div class="card-esp">(.*?)</div>', card),
            'stem_el': grab(r'<div class="q-stem lang-el">(.*?)</div>', card),
            'stem_es': grab(r'<div class="q-stem lang-es">(.*?)</div>', card),
            'options': opts,
            'correct': correct,
            'expl_el': grab(r'<p class="lang-el">(.*?)</p>', expl),
            'expl_es': grab(r'<p class="lang-es">(.*?)</p>', expl),
            'dis_el': grab(r'<p class="lang-el">(.*?)</p>', dis),
            'dis_es': grab(r'<p class="lang-es">(.*?)</p>', dis),
            'cite': grab(r'<div class="q-cite">(?:&#128218;|\U0001F4DA)?\s*(.*?)</div>', card),
        })

    dest = write_out('bank_%s.json' % spec,
                     json.dumps(bank, ensure_ascii=False, indent=1))
    print('spec %s: %d rescatadas, %d plantillas descartadas -> %s'
          % (spec, len(bank), skipped, dest))
    by_sid = {}
    for q in bank:
        by_sid[q['sid']] = by_sid.get(q['sid'], 0) + 1
    for s in sorted(by_sid):
        print('   %-12s %d' % (s, by_sid[s]))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
