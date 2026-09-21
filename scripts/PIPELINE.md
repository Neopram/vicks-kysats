# Pipeline v6 — apps por materia

Las tres apps de materia (`patologia/`, `pediatria/`, `cirugia/`) **se compilan**, no
se editan a mano. La app raíz `index.html` es la plantilla del motor y **no se toca nunca**:
ahí vive el progreso real del usuario (`BK_APP = 'vicks-kysats'`, 322 preguntas A-1…C-116).

```
index.html  (motor, intocable)  ─┐
content/bank_A.json              ├─► scripts/build.sh ─► patologia/index.html + sw.js + manifest.json
content/bank_B.json              │                       pediatria/…
content/bank_C.json             ─┘                       cirugia/…
```

## Uso

```bash
./scripts/build.sh            # valida, compila y verifica A, B y C
./scripts/build.sh B          # solo Pediatría
./scripts/build.sh --no-check # salta la puerta de calidad (no usar para publicar)
```

## Qué hace el compilador

Para cada materia, partiendo de la app raíz:

1. Elimina del DOM las secciones de las otras dos materias y sus bloques de navegación.
2. Rellena las secciones propias con las tarjetas del banco JSON.
3. Filtra `SECT`, `SPEC`, `REFS`, `PRESETS`, `SOURCES` a la materia.
4. Filtra `CNODES` y `CONCEPTS` por `sid`, y **reconstruye los arrays `q`** de cada
   concepto con los ids del banco nuevo, para que el mapa y el BKT funcionen.
5. Filtra `GLOSS_RAW` por los códigos de sección (`pc`, `bn`, `sa`…).
6. Fija `BK_APP` propio (`vicks-kysats-v6-{A,B,C}`) y un `CACHE` propio en `sw.js`.

## Por qué existe la puerta de calidad

El validador anterior (`validate_vicks_v6.py`, en el directorio padre) solo comprobaba el
esquema: que existiera una `.q-cite`, no que la cita fuera real; que `data-correct` estuviera
entre 0 y 4, no que no fuera siempre 0. Por ahí se colaron 698 tarjetas plantilla
(«Pregunta sobre X» / «Incorrecto 1…4»), todas marcadas *Revisada* con probabilidad alta.

`scripts/validate_bank.py` rechaza:

| Regla | Motivo |
|---|---|
| Patrones plantilla en enunciado, opciones o explicación | Es lo que se coló |
| Opción que se autodelata («… - Respuesta correcta») | Ídem |
| Cita sin año, edición ni fuente reconocible | «Pediatric Reference - X» no es una cita |
| Enunciado < 40 car., explicación < 40, distractores < 30 | Relleno |
| Opciones repetidas dentro de una pregunta | Descarta la opción sin saber |
| Enunciado duplicado entre preguntas | Contenido clonado |
| La correcta en la misma posición > 35 % de las veces | Las 1000 viejas tenían `data-correct="0"` |
| Id fuera de rango o que pise A/B/C-1…103 | Colisión con el progreso de la raíz |
| `sid` que no pertenece a la materia | Es lo que producía el «0P» |

`scripts/check_build.py` se ejecuta sobre el HTML ya compilado y reproduce lo que hace
`parseQuestions()`: contar `.card` dentro de cada `<section id=…>` listado en `SECT`.
**Ese es el camino real por el que la app cuenta preguntas — el atributo `data-sid` no lo
lee nadie.** Cualquier sección de `SECT` con cero tarjetas dentro sale como «0P» en la
navegación, y el verificador lo marca como error.

## Formato del banco

`content/bank_{A,B,C}.json` es una lista de objetos:

```json
{
  "id": "A-104",
  "sid": "path-cardio",
  "concepts": ["c.path.cardio.sca"],
  "prob": 88,
  "topic_el": "…", "topic_es": "…",
  "stem_el": "…",  "stem_es": "…",
  "options": [{"el": "…", "es": "…"}, … 5],
  "correct": 2,
  "expl_el": "…", "expl_es": "…",
  "dis_el": "…",  "dis_es": "…",
  "cite": "Harrison 21.ª ed., cap. «Insuficiencia cardíaca»"
}
```

`scripts/extract_bank.py <index.html> <spec>` hace el camino inverso: recupera las preguntas
de un HTML existente a JSON, descarta las plantillas y rebaraja las opciones de forma
determinista para romper el sesgo de posición.

## Nota de entorno (Windows)

Controlled Folder Access impide que `python.exe` **cree** archivos dentro de `Desktop`.
Falla como `FileNotFoundError` sobre una ruta cuyo directorio padre sí existe, lo cual
despista. Por eso los scripts de Python escriben en `%TEMP%/vicks_build` y `build.sh`
copia al repo con `cp`, que sí está permitido. Por lo mismo fallan `sed -i` y `perl -i`.
