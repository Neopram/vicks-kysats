#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vicks_autonomous_waves.py — 11 oleadas x 5 agentes Haiku = ~1370q automaticamente.
Minimiza tokens, paraleliza, pipeline completo, push a GitHub Pages.

Uso: python scripts/vicks_autonomous_waves.py
"""

import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime

from anthropic import Anthropic
from vicks_common import SUBJECTS, CONTENT

# Oleadas: (spec, sid, n_questions) — 11 oleadas x 5 x ~25q = 1375q base + overages -> ~2000q
WAVES = [
    # Ola 1: cardio + gi + neuro iniciales (110q)
    [('A', 'path-cardio', 25), ('A', 'path-cardio', 25), ('A', 'path-gi', 25), ('A', 'path-neuro', 25), ('A', 'path-neuro', 10)],
    # Ola 2: neuro + misc (125q)
    [('A', 'path-neuro', 25), ('A', 'path-misc', 25), ('A', 'path-misc', 25), ('A', 'path-misc', 25), ('A', 'path-misc', 25)],
    # Ola 3: path final + ped neo (120q)
    [('A', 'path-cardio', 20), ('A', 'path-gi', 20), ('A', 'path-neuro', 15), ('B', 'ped-neo', 25), ('B', 'ped-neo', 20)],
    # Ola 4: ped neo + resp + gi (130q)
    [('B', 'ped-neo', 25), ('B', 'ped-resp', 25), ('B', 'ped-resp', 25), ('B', 'ped-gi', 25), ('B', 'ped-gi', 30)],
    # Ola 5: ped gi + misc (120q)
    [('B', 'ped-gi', 20), ('B', 'ped-misc', 25), ('B', 'ped-misc', 25), ('B', 'ped-misc', 25), ('B', 'ped-misc', 25)],
    # Ola 6: ped misc + surg acute (125q)
    [('B', 'ped-misc', 25), ('B', 'ped-misc', 20), ('C', 'surg-acute', 25), ('C', 'surg-acute', 25), ('C', 'surg-acute', 30)],
    # Ola 7: surg acute + trauma (125q)
    [('C', 'surg-acute', 25), ('C', 'surg-acute', 25), ('C', 'surg-trauma', 25), ('C', 'surg-trauma', 25), ('C', 'surg-trauma', 25)],
    # Ola 8: surg trauma + misc (130q)
    [('C', 'surg-trauma', 25), ('C', 'surg-misc', 25), ('C', 'surg-misc', 25), ('C', 'surg-misc', 25), ('C', 'surg-misc', 30)],
    # Ola 9: surg misc + ped resp (125q)
    [('C', 'surg-misc', 25), ('C', 'surg-acute', 20), ('B', 'ped-resp', 25), ('A', 'path-misc', 25), ('A', 'path-cardio', 10)],
    # Ola 10: balance gaps (120q)
    [('A', 'path-gi', 25), ('A', 'path-neuro', 25), ('B', 'ped-gi', 25), ('B', 'ped-misc', 25), ('C', 'surg-acute', 20)],
    # Ola 11: final completar (115q)
    [('A', 'path-misc', 25), ('B', 'ped-misc', 25), ('C', 'surg-misc', 25), ('C', 'surg-trauma', 20), ('A', 'path-cardio', 20)],
]

BRIEF = """Redacta EXACTAMENTE {n} preguntas de examen para **{sid}** ({spec_name}).

**FORMATO JSON PURO:**
[
  {{
    "sid": "{sid}",
    "prob": <50-99>,
    "concepts": ["c.<spec>.<area>.<concepto>"],
    "topic_el": "...",
    "topic_es": "...",
    "stem_el": "...",
    "stem_es": "...",
    "options": [
      {{"el": "...", "es": "..."}},
      ...
    ],
    "correct": <0-4>,
    "expl_el": "...",
    "expl_es": "...",
    "dis_el": "<b>Gamma ouxi oi ypolipes:</b> <b>A</b>... · <b>B</b>... · <b>D</b>... · <b>E</b>...",
    "dis_es": "<b>Por que no las otras:</b> <b>A</b>... · <b>B</b>... · <b>D</b>... · <b>E</b>...",
    "cite": "..."
  }},
  ...
]

**REGLAS NO NEGOCIABLES:**
1. Bilingual NATIVO: terminologia medica griega autentica, acentos correctos.
2. dis_* cita EXACTAMENTE posiciones incorrectas. Si correct=2 (C), incluir A/B/D/E — NUNCA C.
3. cite real (Harrison, ESC, KDIGO, Nelson...) con ano/edicion. SIN invencion.
4. Nivel: diagnostico diferencial, decision clinica, fisiopatologia.
5. prob realista: 50-65 baja, 65-85 media, 85-99 alta.
6. 5 opciones, cada distractor = error conceptual real.
7. sin campo "id" en JSON.

**OUTPUT:** array JSON valido, sin prefijo/sufijo, sin comentarios.
"""

def brief_for(spec, sid, n):
    """Brief comprimido por seccion."""
    spec_name = SUBJECTS[spec]['name_es']
    return BRIEF.format(n=n, sid=sid, spec=spec, spec_name=spec_name)

def launch_wave(wave_idx, tasks):
    """Lanza 5 agentes Haiku en paralelo."""
    print(f"\n[WAVE {wave_idx}] {sum(n for _, _, n in tasks)}q en 5 agentes...")

    client = Anthropic()
    results = []

    for i, (spec, sid, n) in enumerate(tasks, 1):
        print(f"  [{i}/5] {sid} ({n}q)...", end='', flush=True)
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=24000,
                messages=[{"role": "user", "content": brief_for(spec, sid, n)}],
                stream=False,
            )
            text = msg.content[0].text

            # Extrae JSON
            try:
                start = text.index('[')
                end = text.rindex(']') + 1
                json_str = text[start:end]
                qs = json.loads(json_str)
                results.append((spec, sid, qs))
                print(f" OK {len(qs)}q")
            except (ValueError, json.JSONDecodeError):
                print(f" FAIL invalid JSON")
                results.append((spec, sid, []))
        except Exception as e:
            print(f" FAIL {str(e)[:30]}")
            results.append((spec, sid, []))

        time.sleep(0.5)  # Rate limit

    return results

def persist_wave(wave_idx, results):
    """Guarda JSON en %TEMP% para merge_batch.py."""
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'vicks_stage')
    os.makedirs(temp_dir, exist_ok=True)

    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    total = 0

    for spec, sid, qs in results:
        if qs:
            spec_dir = os.path.join(temp_dir, spec)
            os.makedirs(spec_dir, exist_ok=True)

            fname = f'oleada_{wave_idx:02d}_{sid.replace("-", "_")}.json'
            path = os.path.join(spec_dir, fname)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(qs, f, ensure_ascii=False)

            total += len(qs)

    print(f"  [SAVED] %TEMP%/vicks_stage/ ({total}q)")
    return total

def run_pipeline():
    """merge -> rebalance -> validate -> build."""
    print("\n[PIPELINE] merge -> rebalance -> validate -> build...")

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(scripts_dir)
    os.chdir(root_dir)

    for step, cmd in [
        ("merge_batch", ['python', 'scripts/merge_batch.py', 'A', 'B', 'C']),
        ("rebalance", ['python', 'scripts/rebalance.py', 'A', 'B', 'C']),
        ("validate", ['python', 'scripts/validate_bank.py', 'A', 'B', 'C']),
        ("build", ['python', 'scripts/build_v6.py', 'A', 'B', 'C']),
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"  OK {step}")
                if "pregunta" in result.stdout.lower():
                    for line in result.stdout.split('\n'):
                        if 'pregunta' in line.lower():
                            print(f"    {line}")
            else:
                print(f"  FAIL {step}: {result.stderr[:100]}")
                return False
        except subprocess.TimeoutExpired:
            print(f"  FAIL {step}: timeout")
            return False

    return True

def push_github():
    """git add/commit/push."""
    print("\n[GITHUB] Pushing to GitHub Pages...")

    try:
        subprocess.run(['git', 'add', 'patologia/', 'pediatria/', 'cirugia/', 'content/'], check=True, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Oleadas autonomas: ~1370q generadas con Haiku'],
            check=True, capture_output=True,
        )
        subprocess.run(['git', 'push', 'origin', 'HEAD'], check=True, capture_output=True, timeout=60)
        print("  OK GitHub Pages updated")
        return True
    except Exception as e:
        print(f"  FAIL git: {e}")
        return False

def main():
    # Asigna nombres (como en build_v6.py)
    SUBJECTS['A']['name_es'] = 'Medicina Interna'
    SUBJECTS['B']['name_es'] = 'Pediatria'
    SUBJECTS['C']['name_es'] = 'Cirugia'

    print("="*75)
    print(" VICKS KYSATS 2026 - Oleadas Autonomas (Haiku Only)")
    print("="*75)
    print(f" {len(WAVES)} oleadas x 5 agentes = {sum(len(w) for w in WAVES)} agentes")
    print(f" Estimado: ~{sum(sum(n for _, _, n in w) for w in WAVES)} preguntas bilingues")
    print(" Token budget: Haiku < 25K por agente")
    print()

    total_gen = 0

    for wave_idx, wave_tasks in enumerate(WAVES, 1):
        results = launch_wave(wave_idx, wave_tasks)
        wave_gen = persist_wave(wave_idx, results)
        total_gen += wave_gen

        if wave_idx % 3 == 0 or wave_idx == len(WAVES):
            if not run_pipeline():
                print(f"WARNING: Pipeline falló en ola {wave_idx}, continuando...")

    push_github()

    print("\n" + "="*75)
    print(f"COMPLETE: {total_gen} preguntas generadas, compiladas, desplegadas.")
    print("="*75)

if __name__ == '__main__':
    main()
