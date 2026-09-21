# -*- coding: utf-8 -*-
"""Compila las apps por materia (patologia / pediatria / cirugia) a partir de
la app raiz como plantilla de motor + un banco de preguntas en JSON.

La app raiz NO se toca nunca: se lee y se deriva.

Uso:  python build_v6.py [A B C]   -> escribe en OUT_DIR/<dir>/
"""

import json
import os
import re
import sys

from vicks_common import (CONTENT, OUT_DIR, SUBJECTS, filter_js_lines,
                          js_block, read_template, replace_js, write_out)

CODES = {}          # sid -> code (pc, bn, sa...)  se rellena desde la plantilla


# ------------------------------------------------------------------ tarjeta --
def render_card(q, subj):
    cls = 'prob-high' if q['prob'] >= 85 else ('prob-med' if q['prob'] >= 65 else 'prob-low')
    opts = '\n'.join(
        '      <li onclick="selectOption(this)"><span class="opt-letter">%s</span>'
        '<div class="opt-text"><span class="lang-el">%s</span>'
        '<span class="lang-es">%s</span></div></li>'
        % (chr(65 + i), o['el'], o['es'])
        for i, o in enumerate(q['options']))
    dis = ''
    if q.get('dis_el') or q.get('dis_es'):
        dis = ('\n      <div class="q-dis"><p class="lang-el">%s</p>'
               '<p class="lang-es">%s</p></div>'
               % (q.get('dis_el', ''), q.get('dis_es', '')))
    esp = ''
    if q.get('topic_es'):
        esp = '\n    <div class="card-esp">%s</div>' % q['topic_es']
    return '''  <div class="card" data-src="%(src)s" data-concepts="%(con)s" data-review="ok">
    <div class="card-header"><span class="card-number">%(id)s</span><span class="card-specialty spec-%(cls)s">%(subj)s</span><span class="vbadge v-ed" title="Redactada editorialmente a partir de guias y libros de referencia; no procede de un examen oficial">Editorial</span><span class="vbadge v-rev v-ok" title="Revision clinica: respuesta y distractores contrastados con la referencia citada">Revisada</span>
      <span class="prob %(pcls)s">%(prob)d%%</span>
    </div>
    <div class="card-greek">%(tel)s</div>%(esp)s
    <div class="q-stem lang-el">%(sel)s</div>
    <div class="q-stem lang-es">%(ses)s</div>
    <ul class="q-options" data-correct="%(cor)d">
%(opts)s
    </ul>
    <div class="q-explanation" hidden>
      <p class="lang-el">%(xel)s</p>
      <p class="lang-es">%(xes)s</p>%(dis)s
      <div class="q-cite">\U0001F4DA %(cite)s</div>
    </div>
    <div class="q-actions"><button class="btn btn-primary" onclick="revealAnswer(this)">\u0391\u03c0\u03ac\u03bd\u03c4\u03b7\u03c3\u03b7 / Respuesta</button></div>
  </div>''' % dict(
        src=q.get('src', 'ed'), con=','.join(q.get('concepts', [])), id=q['id'],
        cls=subj['cls'], subj=subj['name_el'], pcls=cls, prob=q['prob'],
        tel=q.get('topic_el', ''), esp=esp, sel=q['stem_el'], ses=q['stem_es'],
        cor=q['correct'], opts=opts, xel=q.get('expl_el', ''),
        xes=q.get('expl_es', ''), dis=dis, cite=q.get('cite', ''))


# ------------------------------------------------------------------ secciones --
def section_spans(html):
    """[(sid, inicio, fin)] de cada <section id="...">...</section>."""
    spans = []
    for m in re.finditer(r'^<section id="([a-z-]+)"[^>]*>$', html, re.M):
        end = html.index('\n</section>', m.end()) + len('\n</section>')
        spans.append((m.group(1), m.start(), end))
    return spans


def rewrite_sections(html, spec, bank):
    """Borra las secciones de otras materias y rellena las propias."""
    subj = SUBJECTS[spec]
    by_sid = {}
    for q in bank:
        by_sid.setdefault(q['sid'], []).append(q)

    out, pos = [], 0
    for sid, start, end in section_spans(html):
        out.append(html[pos:start])
        pos = end
        if sid in subj['sections']:
            block = html[start:end]
            cut = block.find('\n  <div class="card"')
            if cut == -1:                       # seccion sin tarjetas en plantilla
                cut = block.rindex('\n</section>')
            cards = [render_card(q, subj) for q in by_sid.get(sid, [])]
            out.append(block[:cut] + '\n' + '\n'.join(cards) + '\n</section>')
        elif sid in ALL_FOREIGN:
            pass                                # seccion de otra materia: fuera
        else:
            out.append(html[start:end])         # dashboard, glosario, etc.
    out.append(html[pos:])
    return ''.join(out)


def strip_nav(html, spec):
    """Quita los bloques de navegacion de las otras materias."""
    def drop(m):
        blk = m.group(0)
        sids = re.findall(r'data-count="([a-z-]+)"', blk)
        if sids and all(s not in SUBJECTS[spec]['sections'] for s in sids):
            return ''
        return blk
    return re.sub(r'  <div class="nav-section">\n(?:.*?\n)*?  </div>\n', drop, html)


# ------------------------------------------------------------------ datos JS --
def filter_structures(html, spec, bank):
    subj = SUBJECTS[spec]
    own = set(subj['sections'])
    own_codes = {CODES[s] for s in own}

    html = filter_js_lines(html, 'SECT', lambda ln: any(
        ("'%s'" % s) in ln for s in own))
    html = filter_js_lines(html, 'REFS', lambda ln: any(
        ("'%s'" % s) in ln for s in own))
    html = filter_js_lines(html, 'PRESETS', lambda ln: (
        ("spec:'%s'" % spec) in ln or "spec:'ALL'" in ln))
    html = filter_js_lines(html, 'SOURCES', lambda ln: (
        not re.search(r"secs:\s*\[", ln)
        or any(("'%s'" % s) in ln for s in own)))

    # SPEC: solo la materia propia
    _, _, spec_body = js_block(html, 'SPEC')
    m = re.search(r"%s:\{[^}]*\}" % spec, spec_body)
    html = replace_js(html, 'SPEC', '{ %s }' % m.group(0))

    # CNODES / CONCEPTS: JSON, filtrar por sid
    _, _, body = js_block(html, 'CNODES')
    nodes = [n for n in json.loads(body) if n['sid'] in own]
    html = replace_js(html, 'CNODES', json.dumps(nodes, ensure_ascii=False))

    # los arrays q de CONCEPTS se reconstruyen con los ids del banco nuevo
    qs_by_concept = {}
    for q in bank:
        for c in q.get('concepts', []):
            qs_by_concept.setdefault(c, []).append(q['id'])
    _, _, body = js_block(html, 'CONCEPTS')
    concepts = []
    for c in json.loads(body):
        if c['sid'] not in own:
            continue
        c['q'] = qs_by_concept.get(c['id'], [])
        concepts.append(c)
    # conceptos nuevos que aparecen en el banco y no estaban en la plantilla
    known = {c['id'] for c in concepts}
    nodes_by_sid = {}
    for n in nodes:
        nodes_by_sid.setdefault(n['sid'], n['id'])
    for q in bank:
        for cid in q.get('concepts', []):
            if cid in known:
                continue
            known.add(cid)
            concepts.append({
                'id': cid, 'sid': q['sid'],
                'node': nodes_by_sid.get(q['sid'], (nodes[0]['id'] if nodes else '')),
                'el': q.get('topic_el', cid), 'es': q.get('topic_es', cid),
                'q': qs_by_concept.get(cid, []),
            })
    html = replace_js(html, 'CONCEPTS', json.dumps(concepts, ensure_ascii=False))

    # GLOSS_RAW: literal de plantilla `el|es|sys|codigos`
    m = re.search(r'const GLOSS_RAW = `\n(.*?)\n`;', html, re.S)
    kept = []
    for line in m.group(1).split('\n'):
        parts = line.split('|')
        if len(parts) < 4:
            continue
        codes = [c for c in parts[3].split(',') if c in own_codes]
        if codes:
            kept.append('|'.join(parts[:3] + [','.join(codes)] + parts[4:]))
    html = html[:m.start()] + 'const GLOSS_RAW = `\n%s\n`;' % '\n'.join(kept) + html[m.end():]
    return html


# ------------------------------------------------------------------ assets --
def sw_js(subj, version):
    return """const CACHE = '%s-%s';
const ASSETS = ['./', './index.html', './manifest.json'];
self.addEventListener('install', e => { self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).catch(()=>{})); });
self.addEventListener('activate', e => { e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)
    .then(res => { const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});
      return res; })
    .catch(() => caches.match('./index.html'))));
});
""" % (subj['cache'], version)


def manifest(subj, n):
    return json.dumps({
        'name': 'Vicks \u00b7 %s' % subj['name_el'],
        'short_name': 'Vicks %s' % subj['cls'].capitalize(),
        'description': 'Gu\u00eda adaptativa \u039a\u03a5\u03a3\u0391\u03a4\u03a3 2026 \u2014 %s: %d preguntas nuevas' % (subj['name_es'], n),
        'start_url': './index.html',
        'scope': './',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#F7F6F3',
        'theme_color': '#1B2A4A',
        'icons': [
            {'src': '../icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any maskable'},
            {'src': '../icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
        ],
    }, ensure_ascii=False, indent=2)


# -------------------------------------------------------------------- build --
def build(spec):
    global ALL_FOREIGN
    subj = SUBJECTS[spec]
    html = read_template()

    # codigos de seccion leidos de la plantilla
    _, _, sect_body = js_block(html, 'SECT')
    for sid, code in re.findall(r"'([a-z-]+)':\s*\{[^}]*code:'([a-z]+)'", sect_body):
        CODES[sid] = code

    ALL_FOREIGN = {s for k, v in SUBJECTS.items() if k != spec for s in v['sections']}

    path = os.path.join(CONTENT, 'bank_%s.json' % spec)
    bank = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else []
    bank = [q for q in bank if q['sid'] in subj['sections']]
    bank.sort(key=lambda q: int(q['id'].split('-')[1]))

    html = rewrite_sections(html, spec, bank)
    html = strip_nav(html, spec)
    html = filter_structures(html, spec, bank)

    html = re.sub(r"const BK_APP = '[^']*'", "const BK_APP = '%s'" % subj['bk_app'], html)
    html = re.sub(r'<title>.*?</title>',
                  '<title>Vicks \u00b7 %s \u2014 \u039a\u03a5\u03a3\u0391\u03a4\u03a3 2026</title>' % subj['name_el'],
                  html, count=1, flags=re.S)

    version = '%08x' % (abs(hash(html)) & 0xFFFFFFFF)
    write_out('%s/index.html' % subj['dir'], html)
    write_out('%s/sw.js' % subj['dir'], sw_js(subj, version))
    write_out('%s/manifest.json' % subj['dir'], manifest(subj, len(bank)))

    by_sid = {}
    for q in bank:
        by_sid[q['sid']] = by_sid.get(q['sid'], 0) + 1
    print('%-10s %4d preguntas  %s' % (
        subj['dir'], len(bank),
        ' '.join('%s=%d/%d' % (s.split('-')[1], by_sid.get(s, 0), subj['sections'][s])
                 for s in subj['sections'])))


if __name__ == '__main__':
    # nombres griegos reales (fuera de vicks_common para no pelear con encodings)
    SUBJECTS['A']['name_el'] = '\u03a0\u03b1\u03b8\u03bf\u03bb\u03bf\u03b3\u03af\u03b1'
    SUBJECTS['A']['name_es'] = 'Medicina Interna'
    SUBJECTS['B']['name_el'] = '\u03a0\u03b1\u03b9\u03b4\u03b9\u03b1\u03c4\u03c1\u03b9\u03ba\u03ae'
    SUBJECTS['B']['name_es'] = 'Pediatr\u00eda'
    SUBJECTS['C']['name_el'] = '\u03a7\u03b5\u03b9\u03c1\u03bf\u03c5\u03c1\u03b3\u03b9\u03ba\u03ae'
    SUBJECTS['C']['name_es'] = 'Cirug\u00eda'
    for s in (sys.argv[1:] or ['A', 'B', 'C']):
        build(s)
    print('salida en', OUT_DIR)
