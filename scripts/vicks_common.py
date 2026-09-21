# -*- coding: utf-8 -*-
"""Definiciones compartidas por el pipeline v6 de Vicks KYSATS 2026.

Nota de entorno: en este PC Controlled Folder Access impide que python.exe
*cree* archivos dentro de Desktop/Documents. Estos scripts escriben siempre
en OUT_DIR (%TEMP%) y build.sh copia el resultado al repo con `cp`.
"""

import os
import re

ROOT = os.environ.get(
    'VICKS_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE = os.path.join(ROOT, 'index.html')
CONTENT = os.path.join(ROOT, 'content')

# Directorio de salida: %TEMP%/vicks_build (python si puede escribir ahi)
OUT_DIR = os.path.join(os.environ.get('TEMP', '/tmp'), 'vicks_build')

# ---------------------------------------------------------------- materias --
SUBJECTS = {
    'A': {
        'dir': 'patologia',
        'prefix': 'path',
        'bk_app': 'vicks-kysats-v6-A',
        'cache': 'vicks-v6-path',
        'cls': 'path',
        'date': '2026-10-12',
        # sid -> nº de preguntas objetivo (pesos DOATAP 2024 sobre 1000)
        'sections': {
            'path-cardio': 130,
            'path-resp': 50,
            'path-gi': 130,
            'path-misc': 390,
            'path-neuro': 300,
        },
    },
    'B': {
        'dir': 'pediatria',
        'prefix': 'ped',
        'bk_app': 'vicks-kysats-v6-B',
        'cache': 'vicks-v6-ped',
        'cls': 'ped',
        'date': '2026-10-16',
        'sections': {
            'ped-neo': 200,
            'ped-resp': 220,
            'ped-gi': 190,
            'ped-misc': 390,
        },
    },
    'C': {
        'dir': 'cirugia',
        'prefix': 'surg',
        'bk_app': 'vicks-kysats-v6-C',
        'cache': 'vicks-v6-surg',
        'cls': 'surg',
        'date': '2026-10-21',
        'sections': {
            'surg-acute': 480,
            'surg-trauma': 180,
            'surg-misc': 340,
        },
    },
}

ALL_SIDS = {sid for s in SUBJECTS.values() for sid in s['sections']}

# Las preguntas nuevas empiezan en 104: A-1..A-103 / B-1..B-103 / C-1..C-116
# viven en la app raiz y no se duplican aqui.
FIRST_ID = 104


def spec_of(sid):
    for letter, s in SUBJECTS.items():
        if sid in s['sections']:
            return letter
    raise KeyError(sid)


def read_template():
    with open(TEMPLATE, encoding='utf-8') as fh:
        return fh.read()


def write_out(relpath, text):
    """Escribe en OUT_DIR/relpath y devuelve la ruta absoluta."""
    path = os.path.join(OUT_DIR, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    return path


# ------------------------------------------------------------ JS structures --
def js_block(html, name):
    """Devuelve (inicio, fin, cuerpo) de `const NAME = ...;` en el HTML."""
    m = re.search(r'^const ' + name + r' = (.*?);[ \t]*$', html, re.M | re.S)
    if not m:
        raise ValueError('no encuentro const %s' % name)
    return m.start(), m.end(), m.group(1)


def replace_js(html, name, new_body):
    start, end, _ = js_block(html, name)
    return html[:start] + 'const %s = %s;' % (name, new_body) + html[end:]


def filter_js_lines(html, name, keep):
    """Filtra un objeto/array JS multilinea conservando las lineas cuyo
    contenido satisface keep(line). Primera y ultima linea se mantienen."""
    start, end, body = js_block(html, name)
    lines = body.split('\n')
    mid = [ln for ln in lines[1:-1] if keep(ln)]
    if mid:
        mid[-1] = re.sub(r',\s*$', '', mid[-1])
    out = [lines[0]] + mid + [lines[-1]]
    return html[:start] + 'const %s = %s;' % (name, '\n'.join(out)) + html[end:]
