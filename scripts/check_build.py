# -*- coding: utf-8 -*-
"""Comprueba el HTML ya compilado: lo que veria el motor al arrancar.

Reproduce lo que hace parseQuestions() —contar .card dentro de cada
<section id=...> listado en SECT— porque ese, y no data-sid, es el camino real
por el que la app cuenta preguntas. Aqui es donde se detecta el "0P".
"""

import json
import os
import re
import sys

from vicks_common import ROOT, SUBJECTS

FOREIGN_OK = {'dashboard', 'exam-hub', 'exam-info', 'glossary', 'map',
              'methodology', 'playlist', 'print', 'progress', 'resources',
              'results', 'retrain', 'schedule', 'source-view'}


def check(spec):
    subj = SUBJECTS[spec]
    path = os.path.join(ROOT, subj['dir'], 'index.html')
    if not os.path.exists(path):
        print('%s: no compilado' % subj['dir'])
        return 1
    html = open(path, encoding='utf-8').read()
    errs = []

    # secciones presentes y tarjetas dentro de cada una
    counts, sid = {}, None
    for line in html.split('\n'):
        m = re.match(r'<section id="([a-z-]+)"', line)
        if m:
            sid = m.group(1)
            counts.setdefault(sid, 0)
        elif 'class="card"' in line and sid:
            counts[sid] = counts.get(sid, 0) + 1

    present = set(counts)
    foreign = present - set(subj['sections']) - FOREIGN_OK
    if foreign:
        errs.append('secciones de otra materia todavia en el DOM: %s' % sorted(foreign))

    # SECT debe listar exactamente las secciones propias
    sect = re.search(r'^const SECT = \{(.*?)\n\};', html, re.M | re.S).group(1)
    sect_keys = set(re.findall(r"'([a-z-]+)':", sect))
    if sect_keys != set(subj['sections']):
        errs.append('SECT lista %s, deberia listar %s'
                    % (sorted(sect_keys), sorted(subj['sections'])))

    # toda seccion de SECT con 0 tarjetas saldra como "0P" en la navegacion
    zeros = [s for s in sect_keys if counts.get(s, 0) == 0]
    if zeros:
        errs.append('secciones a 0P en la navegacion: %s' % sorted(zeros))

    # aislamiento del progreso
    bk = re.search(r"const BK_APP = '([^']*)'", html).group(1)
    if bk != subj['bk_app']:
        errs.append('BK_APP="%s", deberia ser "%s" (colision de progreso)'
                    % (bk, subj['bk_app']))
    cache = re.search(r"const CACHE = '([^']*)'",
                      open(os.path.join(ROOT, subj['dir'], 'sw.js'),
                           encoding='utf-8').read()).group(1)
    if not cache.startswith(subj['cache']):
        errs.append('CACHE del service worker "%s" no aislado' % cache)

    # rastros de contenido plantilla
    for pat in ('Pregunta sobre ', 'Incorrecto 1<', 'Respuesta correcta<'):
        n = html.count(pat)
        if n:
            errs.append('quedan %d rastros de plantilla ("%s")' % (n, pat.strip('<')))

    # ids unicos
    # solo ids reales: los ${...} son literales de plantilla del motor
    ids = re.findall(r'class="card-number">([ABC]-\d+)<', html)
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append('ids duplicados en el HTML: %s' % sorted(dup)[:5])

    total = sum(counts.get(s, 0) for s in subj['sections'])
    print('%-10s %4d preguntas  %s' % (
        subj['dir'], total,
        '  '.join('%s=%d' % (s.split('-')[1], counts.get(s, 0))
                  for s in subj['sections'])))
    for e in errs:
        print('   ERROR: %s' % e)
    return len(errs)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a in ('A', 'B', 'C')]
    bad = sum(check(s) for s in (args or ['A', 'B', 'C']))
    if bad:
        print('=> %d problemas' % bad)
    else:
        print('=> compilacion correcta')
    sys.exit(1 if bad else 0)
