# Brief de redacción — preguntas ΚΥ.Σ.Α.Τ.Σ. 2026

Escribes preguntas de examen para el examen de habilitación médica de Chipre
(ΚΥ.Σ.Α.Τ.Σ. 2026). Quien estudia es un médico especialista con 21 años de ejercicio.
**El examen real se celebra únicamente en griego**, y se aprueba con el 50 % en cada
materia por separado.

Nivel: medicina clínica de final de carrera / inicio de residencia. Fisiopatología,
diagnóstico diferencial y **primera conducta**. Evita deliberadamente lo que dependa de
una guía concreta que cambie cada dos años; prioriza lo estable y de alto rendimiento.

## Formato de salida

Un **array JSON** y nada más: sin texto antes ni después, sin ``` alrededor.
Escríbelo con la herramienta Write en la ruta exacta que se te indique.

```json
[
  {
    "sid": "path-cardio",
    "prob": 88,
    "concepts": ["c.path.cardio.sca"],
    "topic_el": "Οξύ στεφανιαίο σύνδρομο · STEMI · Επαναιμάτωση",
    "topic_es": "Síndrome coronario agudo · STEMI · Reperfusión",
    "stem_el": "Άνδρας 62 ετών με οπισθοστερνικό άλγος 40 λεπτών…",
    "stem_es": "Varón de 62 años con dolor retroesternal de 40 minutos…",
    "options": [
      {"el": "Άμεση θρομβόλυση στο παρόν κέντρο", "es": "Trombólisis inmediata en el centro actual"},
      {"el": "…", "es": "…"},
      {"el": "…", "es": "…"},
      {"el": "…", "es": "…"},
      {"el": "…", "es": "…"}
    ],
    "correct": 2,
    "expl_el": "…",
    "expl_es": "…",
    "dis_el": "<b>Γιατί όχι οι υπόλοιπες:</b> <b>A</b> … · <b>B</b> … · <b>D</b> … · <b>E</b> …",
    "dis_es": "<b>Por qué no las otras:</b> <b>A</b> … · <b>B</b> … · <b>D</b> … · <b>E</b> …",
    "cite": "Harrison 21.ª ed., cap. «Infarto agudo de miocardio con elevación del ST» · ESC STEMI 2023"
  }
]
```

No pongas campo `id`: los ids se asignan al fundir el lote.

## Reglas que se comprueban automáticamente

Un lote que las incumpla se descarta sin avisar. La puerta de calidad existe porque una
tanda anterior coló 698 tarjetas con enunciados tipo «Pregunta sobre X» y opciones
«Incorrecto 1…4», todas marcadas como revisadas.

1. **Cinco opciones**, A–E. Ninguna vacía, ninguna repetida dentro de la pregunta.
2. **`correct` varía.** Reparte la respuesta correcta entre las cinco posiciones. Ninguna
   posición puede llevarse más del 35 % del lote. (Las 1000 anteriores tenían todas la A.)
3. **Cada distractor codifica un error conceptual real** que un médico podría cometer:
   la conducta correcta pero a destiempo, el fármaco de la indicación vecina, el criterio
   diagnóstico confundido con otro, el estadio anterior del algoritmo. Nada de rellenos
   obviamente absurdos.
4. **`dis_el` / `dis_es` explican por qué falla cada opción incorrecta**, una por una,
   con la letra en negrita. Es lo que convierte la pregunta en material de estudio.
5. **Las letras de `dis_*` tienen que ser exactamente las opciones incorrectas.** Si la
   correcta es la C, el análisis cita A, B, D y E — nunca la C, y sin saltarse ninguna.
   **Si reordenas las opciones, reetiqueta las letras del análisis en el mismo paso.** Un
   agente anterior reordenó para repartir la correcta y dejó el `dis_*` apuntando a las
   letras viejas: sus 19 preguntas explicaban por qué falla la respuesta correcta. Se
   descartaron enteras. Lo más seguro es **decidir la posición de la correcta antes de
   escribir el análisis** y no tocarla después.
6. **`cite` tiene que ser una referencia real y comprobable**, con año o edición:
   `Harrison 21.ª ed., cap. «…»`, `Davidson's 24.ª ed. — cap. «…»`, `ESC 2023`,
   `KDIGO 2012`, `Nelson 21.ª ed., cap. «…»`, `ATLS 10.ª ed.`, `Sabiston 21.ª ed.`.
   **No inventes citas.** Si no estás seguro de un capítulo concreto, cita el libro y la
   edición sin capítulo, o la guía y su año. Una cita falsa es peor que una genérica.
7. **Bilingüe nativo.** El griego se redacta como griego médico, no como traducción
   calcada del español. Usa la terminología griega real (Οξύ έμφραγμα μυοκαρδίου,
   καρδιακή ανεπάρκεια, νεφρική ανεπάρκεια…). Con acentos correctos, en ambos idiomas.
8. **Enunciado ≥ 40 caracteres, explicación ≥ 40, distractores ≥ 30.** En la práctica el
   enunciado será un caso clínico de dos o tres líneas con los datos que hacen falta para
   decidir: edad, cuadro, constantes, la prueba clave.
9. **Sin duplicados.** Ni entre sí ni con temas repetidos con otras palabras. Cada
   pregunta cubre un punto de decisión distinto.
10. **`prob`** entre 50 y 99: tu estimación de cuán probable es que ese punto caiga en el
   examen. Reserva ≥ 88 para el núcleo de alto rendimiento. Reparte de forma realista,
   no pongas todo a 90.
11. **`concepts`**: uno o dos ids con la forma `c.<materia>.<area>.<concepto>`, en
    minúsculas y sin acentos, p. ej. `c.path.cardio.sca`, `c.surg.acute.apendicitis`.
    Reutiliza el mismo id cuando dos preguntas tratan el mismo concepto — así el mapa de
    progreso agrupa bien.

## El listón

Esta es una pregunta real del banco, y es el nivel mínimo:

> **Enunciado:** Varón de 60 años con insuficiencia cardíaca con fracción de eyección
> reducida, en clase funcional II. ¿Qué grupo farmacológico ha demostrado reducir la
> mortalidad?
> **Opciones:** Digoxina / Diuréticos de asa / **Betabloqueantes** / Antagonistas del
> calcio dihidropiridínicos / Nitratos
> **Explicación:** Betabloqueantes, IECA/ARNI, antagonistas del receptor
> mineralocorticoide e inhibidores de SGLT2 reducen mortalidad. Los diuréticos y la
> digoxina mejoran síntomas, no supervivencia.
> **Por qué no las otras:** **A** La digoxina reduce ingresos, no mortalidad · **B** Los
> diuréticos alivian síntomas, no la supervivencia · **D** Las dihidropiridinas no mejoran
> el pronóstico (verapamilo/diltiazem perjudican) · **E** Los nitratos solos no reducen la
> mortalidad
> **Cita:** Harrison 21.ª ed., cap. «Insuficiencia cardíaca: tratamiento» · ESC 2021/2023

Fíjate en que cada distractor es un fármaco que **sí se usa** en insuficiencia cardíaca:
ahí está la discriminación. Ese es el tipo de distractor que hay que construir.

## Honestidad

Si sobre algún tema no tienes base suficiente para escribir una pregunta correcta con una
cita real, **escribe menos preguntas**. Un lote de 30 buenas vale más que 40 con 10
inventadas. Al final de tu trabajo indica cuántas escribiste y si dejaste algún tema fuera
por falta de certeza.
