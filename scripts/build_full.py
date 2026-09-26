# -*- coding: utf-8 -*-
"""Construye /full/ — app unificada con los 3 bancos (A+B+C) combinados.

  python build_full.py

Lee vicks_build/bank_{A,B,C}.json (o content/ si no existen en vicks_build).
Escribe en %TEMP%/vicks_build/full/{index.html, sw.js, manifest.json}.
BK_APP = 'vicks-kysats-v6-FULL' -> IndexedDB aislado del root y sub-apps.
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vicks_common import (CONTENT, OUT_DIR, SUBJECTS, js_block, replace_js,
                          read_template, write_out)

BK_APP_FULL = 'vicks-kysats-v6-FULL'
CACHE_PREFIX = 'vicks-v6-full'


def src_bank(spec):
    p1 = os.path.join(OUT_DIR, 'bank_%s.json' % spec)
    p2 = os.path.join(CONTENT, 'bank_%s.json' % spec)
    p = p1 if os.path.exists(p1) else p2
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []


def section_spans(html):
    spans = []
    for m in re.finditer(r'^<section id="([a-z-]+)"[^>]*>$', html, re.M):
        end = html.index('\n</section>', m.end()) + len('\n</section>')
        spans.append((m.group(1), m.start(), end))
    return spans


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
    return (
        '  <div class="card" data-src="%(src)s" data-concepts="%(con)s" data-review="ok">\n'
        '    <div class="card-header">'
        '<span class="card-number">%(id)s</span>'
        '<span class="card-specialty spec-%(cls)s">%(subj)s</span>'
        '<span class="vbadge v-ed" title="Editorial">Editorial</span>'
        '<span class="vbadge v-rev v-ok" title="Revisada">Revisada</span>\n'
        '      <span class="prob %(pcls)s">%(prob)d%%</span>\n'
        '    </div>\n'
        '    <div class="card-greek">%(tel)s</div>%(esp)s\n'
        '    <div class="q-stem lang-el">%(sel)s</div>\n'
        '    <div class="q-stem lang-es">%(ses)s</div>\n'
        '    <ul class="q-options" data-correct="%(cor)d">\n%(opts)s\n    </ul>\n'
        '    <div class="q-explanation" hidden>\n'
        '      <p class="lang-el">%(xel)s</p>\n'
        '      <p class="lang-es">%(xes)s</p>%(dis)s\n'
        '      <div class="q-cite">\U0001F4DA %(cite)s</div>\n'
        '    </div>\n'
        '    <div class="q-actions">'
        '<button class="btn btn-primary" onclick="revealAnswer(this)">'
        'Απάντηση / Respuesta'
        '</button></div>\n  </div>'
    ) % dict(
        src=q.get('src', 'ed'), con=','.join(q.get('concepts', [])), id=q['id'],
        cls=subj['cls'], subj=subj['name_el'], pcls=cls, prob=q['prob'],
        tel=q.get('topic_el', ''), esp=esp, sel=q['stem_el'], ses=q['stem_es'],
        cor=q['correct'], opts=opts, xel=q.get('expl_el', ''),
        xes=q.get('expl_es', ''), dis=dis, cite=q.get('cite', ''))


def rewrite_all_sections(html, all_bank):
    sid_to_spec = {}
    for spec, subj in SUBJECTS.items():
        for sid in subj['sections']:
            sid_to_spec[sid] = spec
    by_sid = {}
    for q in all_bank:
        by_sid.setdefault(q['sid'], []).append(q)
    out, pos = [], 0
    for sid, start, end in section_spans(html):
        out.append(html[pos:start])
        pos = end
        spec = sid_to_spec.get(sid)
        if spec:
            subj = SUBJECTS[spec]
            block = html[start:end]
            cut = block.find('\n  <div class="card"')
            if cut == -1:
                cut = block.rindex('\n</section>')
            cards = [render_card(q, subj) for q in by_sid.get(sid, [])]
            out.append(block[:cut] + '\n' + '\n'.join(cards) + '\n</section>')
        else:
            out.append(html[start:end])
    out.append(html[pos:])
    return ''.join(out)


def update_concepts(html, all_bank):
    qs_by_concept = {}
    for q in all_bank:
        for c in q.get('concepts', []):
            qs_by_concept.setdefault(c, []).append(q['id'])
    _, _, body = js_block(html, 'CNODES')
    nodes = json.loads(body)
    nodes_by_sid = {n['sid']: n['id'] for n in nodes}
    _, _, body = js_block(html, 'CONCEPTS')
    concepts = json.loads(body)
    for c in concepts:
        c['q'] = qs_by_concept.get(c['id'], [])
    known = {c['id'] for c in concepts}
    for q in all_bank:
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
    return replace_js(html, 'CONCEPTS', json.dumps(concepts, ensure_ascii=False))


def sw_full(version):
    return (
        "const CACHE = '%s-%s';\n"
        "const ASSETS = ['./', './index.html', './manifest.json'];\n"
        "self.addEventListener('install', e => { self.skipWaiting();\n"
        "  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).catch(()=>{})); });\n"
        "self.addEventListener('activate', e => { e.waitUntil(\n"
        "  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))\n"
        "    .then(() => self.clients.claim())); });\n"
        "self.addEventListener('fetch', e => {\n"
        "  if (e.request.method !== 'GET') return;\n"
        "  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)\n"
        "    .then(res => { const copy = res.clone();\n"
        "      caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});\n"
        "      return res; })\n"
        "    .catch(() => caches.match('./index.html'))));\n"
        "});\n"
    ) % (CACHE_PREFIX, version)


def build():
    SUBJECTS['A']['name_el'] = 'Παθολογία'
    SUBJECTS['A']['name_es'] = 'Medicina Interna'
    SUBJECTS['B']['name_el'] = 'Παιδιατρική'
    SUBJECTS['B']['name_es'] = 'Pediatría'
    SUBJECTS['C']['name_el'] = 'Χειρουργική'
    SUBJECTS['C']['name_es'] = 'Cirugía'

    all_bank = []
    for spec in 'ABC':
        bank = src_bank(spec)
        all_bank.extend(bank)
        cnt = {sid: 0 for sid in SUBJECTS[spec]['sections']}
        for q in bank:
            if q['sid'] in cnt:
                cnt[q['sid']] += 1
        print('Bank %s: %d Q  [%s]' % (
            spec, len(bank),
            '  '.join('%s=%d' % (s.split('-')[1], n) for s, n in cnt.items())))

    all_bank.sort(key=lambda q: (q['sid'], int(q['id'].split('-')[1])))

    html = read_template()
    html = rewrite_all_sections(html, all_bank)
    html = update_concepts(html, all_bank)
    html = html.replace("['A','B','C']", "Object.keys(SPEC)")
    html = re.sub(r"const BK_APP = '[^']*'", "const BK_APP = '%s'" % BK_APP_FULL, html)
    html = re.sub(r'<title>.*?</title>',
                  '<title>Vicks · ΚΥΣΑΤΣ 2026 — Completo</title>',
                  html, count=1, flags=re.S)

    version = '%08x' % (abs(hash(html)) & 0xFFFFFFFF)

    write_out('full/index.html', html)
    write_out('full/sw.js', sw_full(version))

    mf = json.dumps({
        'name': 'Vicks · ΚΥΣΑΤΣ 2026 — Completo',
        'short_name': 'Vicks Full',
        'description': (
            'Guía adaptativa ΚΥΣΑΤΣ 2026 — '
            'Παθολογία + '
            'Παιδιατρική + '
            'Χειρουργική: '
            '%d preguntas' % len(all_bank)),
        'start_url': './index.html',
        'scope': '/vicks-kysats/full/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#F7F6F3',
        'theme_color': '#1B2A4A',
        'icons': [
            {'src': '../icons/icon-192.png', 'sizes': '192x192',
             'type': 'image/png', 'purpose': 'any maskable'},
            {'src': '../icons/icon-512.png', 'sizes': '512x512',
             'type': 'image/png', 'purpose': 'any maskable'},
        ],
    }, ensure_ascii=False, indent=2)
    write_out('full/manifest.json', mf)

    print('FULL: %d Q -> %s/full/' % (len(all_bank), OUT_DIR))
    print('BK_APP: %s  |  CACHE: %s-%s' % (BK_APP_FULL, CACHE_PREFIX, version))


if __name__ == '__main__':
    build()
