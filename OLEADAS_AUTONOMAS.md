# Oleadas Autónomas — Vicks KYSATS 2026

Script único que lanza **todas las oleadas pendientes** de contenido generado con **Haiku solo**, optimizando tokens y tiempo.

## Estado actual (2026-09-23)

| Materia | Preguntas | Objetivo | Falta |
|---|---|---|---|
| **Παθολογία (A)** | 331 | 1000 | 669 |
| **Παιδιατρική (B)** | 418 | 1000 | 582 |
| **Χειρουργική (C)** | 198 | 1000 | 802 |
| **TOTAL** | **947** | **3000** | **2053** |

## Qué hace el script

```
11 oleadas × 5 agentes Haiku × ~25 preguntas/agente
    ↓
~1370 preguntas bilingües (griego/español) nativas
    ↓
[Validación automática: placeholder, letter desync, posición sesgada]
    ↓
Pipeline: merge → rebalance → validate → build
    ↓
Tres apps compiladas (patologia/, pediatria/, cirugia/)
    ↓
GitHub Pages: neopram.github.io/vicks-kysats/{patologia,pediatria,cirugia}
```

## Cómo ejecutar

**Requisitos:**
- Python 3.8+
- Git configurado
- `ANTHROPIC_API_KEY` en variables de entorno (Haiku barato, sin límite de uso)

**Lanzar:**

```powershell
cd "C:\Users\feder\Desktop\Banco de preguntas\repo_vicks"
.\launch-waves.ps1
```

**Salida esperada:**

```
=================================================
 VICKS KYSATS 2026 — Oleadas Autónomas
=================================================

✓ Python: Python 3.11.x
✓ Git: git version 2.x
✓ ANTHROPIC_API_KEY configurada

Iniciando oleadas...

🌊 Oleada 1: 110q en 5 agentes...
  [1/5] path-cardio (25q)... ✓ 25q
  [2/5] path-cardio (25q)... ✓ 25q
  [3/5] path-gi (25q)... ✓ 25q
  [4/5] path-neuro (25q)... ✓ 25q
  [5/5] path-neuro (10q)... ✓ 10q
  → Guardado en %TEMP%/vicks_stage/ (110q)

⚙️  Pipeline: merge → rebalance → validate → build...
  ✓ merge_batch
  ✓ rebalance
  ✓ validate
  ✓ build
    patologia   331 preguntas  cardio=76/130 resp=50/50 gi=65/130 misc=83/390 neuro=57/300

🌊 Oleada 2: 125q en 5 agentes...
[...]

✅ COMPLETO: 1370 preguntas generadas, compiladas, desplegadas.
```

## Optimización de tokens

| Aspecto | Estrategia |
|---|---|
| **Modelo** | Haiku 4.5 only (sin Sonnet, sin Opus) |
| **Por agente** | Max 25q ≈ 24K tokens (safety margin) |
| **Brief** | Comprimido, sin ejemplos repetidos |
| **Pipeline** | Cada 3 oleadas (paralelización local) |
| **Salida** | JSON puro, sin explicaciones en texto |
| **Costo** | ~55 × $0.80/1M = $0.04 total |

## Estructura de salida

```
repo_vicks/
  patologia/
    index.html       ← 331 → 600+ preguntas
    sw.js            ← CACHE='vicks-v6-path-{hash}'
    manifest.json
  pediatria/
    index.html       ← 418 → 750+ preguntas
    sw.js            ← CACHE='vicks-v6-ped-{hash}'
    manifest.json
  cirugia/
    index.html       ← 198 → 600+ preguntas
    sw.js            ← CACHE='vicks-v6-surg-{hash}'
    manifest.json
  content/
    bank_A.json      ← Patología compilada + validada
    bank_B.json      ← Pediatría compilada + validada
    bank_C.json      ← Cirugía compilada + validada
```

Cada app es instalable como PWA independiente desde iPhone/Android.

## Quality Gate (automático)

Todas las preguntas pasan validación:

✅ **11 reglas**
1. Bilingual nativo (no traducción)
2. Letra de `dis_*` = posiciones incorrectas exactas
3. Citas verificables (no inventadas)
4. Nivel: diagnóstico diferencial y decisión clínica
5. `prob` realista (50-99, no sesgada)
6. 5 opciones, cada distractor = error real
7. Longitud mínima (40 chars stem, 40 expl, 30 distractor)
8. Sin duplicados (normalización Unicode + dedup)
9. Posición correcta ≤35% por sección (rebalance)
10. Concepto IDs válidos y reutilizables
11. Esquema JSON válido

❌ **Rechazo automático** si:
- Placeholder ("Pregunta sobre...", "Incorrecto N...")
- Distractor letra desync (ej: correct=C pero dis_* cita C)
- Cita falsa o sin año
- Position bias > 35%
- Enunciado autode-traidor (la opción correcta citada en stem)

## Estadísticas esperadas

Tras 11 oleadas:

| Materia | Antes | Después | Δ |
|---|---|---|---|
| **Patología** | 331 | ~700-750 | +369-419 |
| **Pediatría** | 418 | ~750-800 | +332-382 |
| **Cirugía** | 198 | ~600-650 | +402-452 |
| **TOTAL** | 947 | 2050-2200 | +1103-1253 |

Estimado: **~68-73% de cobertura** hacia 3000. Para completar:
- 2-3 oleadas más focalizadas en déficit específico (path-misc, surg-acute)
- O escalar a 30q/agente en próximas rondas

## Troubleshooting

| Problema | Solución |
|---|---|
| `ANTHROPIC_API_KEY no definida` | `$env:ANTHROPIC_API_KEY = "sk-..."` en PowerShell |
| Agente Haiku falla con JSON | Red flag de brief; ver terminal para prompt completo |
| Pipeline merge_batch falla | Revisar %TEMP%/vicks_stage/ si los JSON son válidos |
| Git push falla | `git status` en Terminal; verificar auth SSH |
| Windows Controlled Folder Access bloquea | Scripts escriben en %TEMP%, no Desktop — OK |

## Timeline estimado

- **Lanzamiento:** ~5 min (carga de brevedad)
- **Oleada 1-3:** ~15-20 min (Haiku para génesis)
- **Pipeline merge:** ~2 min (merge JSON + dedup)
- **Rebalance:** ~1 min (shuffling determinístico)
- **Validate:** ~1 min (11 reglas × 1370q)
- **Build:** ~2 min (render HTML × 3 apps)
- **Git push:** ~1 min
- **Total:** ~25-30 min para todas las oleadas

## Monitoreo

Durante ejecución, monitorea:

```powershell
# Terminal 1: Oleadas
.\launch-waves.ps1

# Terminal 2: Monitor de archivos (opcional)
Watch-Item -Path .\content\ -Filter "*.json" | % { Write-Host $_.FullPath }

# Terminal 3: Verificar banco actualizado
Get-Content content/bank_A.json | jq 'length'  # Debe crecer cada oleada
```

## Después: próximos pasos

1. **Verificar en vivo:** Abrir neopram.github.io/vicks-kysats/patologia en navegador
2. **Instalar PWA:** iOS: Share → Add to Home Screen; Android: Menu → Install
3. **Hacer quiz:** Responder 10-20 preguntas, verificar progreso persiste en IndexedDB
4. **Oleadas adicionales:** Si déficit persiste > 30%, lanzar 2-3 oleadas focalizadas
5. **Examen simulado:** SIM-A-I, SIM-B-I, SIM-C-I listos en presets

---

**Script: `scripts/vicks_autonomous_waves.py`**
**Launcher: `launch-waves.ps1`**
**Última actualización: 2026-09-23**
