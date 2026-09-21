# Vicks ΚΥΣΑΤΣ 2026 — versión instalable (PWA, sin conexión)

Cuatro aplicaciones independientes, todas instalables y utilizables sin Internet:

| Ruta | Qué es | Progreso (IndexedDB) |
|---|---|---|
| `index.html` | **App completa.** Las tres materias, 322 preguntas (A-1…A-103, B-1…B-103, C-1…C-116). | `vicks-kysats` |
| `patologia/` | Solo Παθολογία, preguntas nuevas (A-104…) | `vicks-kysats-v6-A` |
| `pediatria/` | Solo Παιδιατρική, preguntas nuevas (B-104…) | `vicks-kysats-v6-B` |
| `cirugia/` | Solo Χειρουργική, preguntas nuevas (C-117…) | `vicks-kysats-v6-C` |

Cada una tiene su propio `manifest.json`, su `sw.js` con un nombre de caché distinto y su
propio espacio de IndexedDB, así que **se pueden instalar las cuatro a la vez y ninguna
pisa el progreso de otra**. Los ids de pregunta no se solapan entre la app raíz y las de
materia.

El progreso se guarda en el propio dispositivo tras cada respuesta. No hay servidor,
cuentas ni envío de datos.

## Publicada en https://neopram.github.io/vicks-kysats/

En el iPhone: abre la URL en **Safari** → Compartir → **Añadir a pantalla de inicio**.
Para una materia suelta, añade la subcarpeta: `…/vicks-kysats/patologia/`.

Para actualizar: haz push de los archivos; la app se actualiza sola en la siguiente
apertura con conexión.

## Las apps de materia se compilan, no se editan

`patologia/index.html`, `pediatria/index.html` y `cirugia/index.html` son **generados**.
No los edites a mano: el siguiente build sobrescribe los cambios.

```bash
./scripts/build.sh          # valida, compila y verifica las tres
./scripts/build.sh B        # solo Pediatría
```

El contenido vive en `content/bank_{A,B,C}.json` y el motor sale de `index.html`, que
actúa de plantilla y **no se modifica nunca**. Todo el detalle está en
[`scripts/PIPELINE.md`](scripts/PIPELINE.md), incluida la puerta de calidad que rechaza
preguntas plantilla, citas no verificables y sesgo de posición de la respuesta correcta.

## Servidor local para probar

```
python -m http.server 8080
```

Abre `http://localhost:8080/`. Sirve para probar la instalación y el modo offline en el
portátil. Para el iPhone hacen falta la misma red y la IP del ordenador
(`http://192.168.x.x:8080/`), pero el service worker solo se registra en `localhost` o en
`https`, así que ahí la caché offline no se activará: usa GitHub Pages.

## Comprobar que funciona sin conexión

1. Abre la guía con conexión una vez (se cachea).
2. Activa el modo avión y vuelve a abrirla: debe cargar y mostrar «⚡ offline» arriba.
3. Responde preguntas, cierra la app del todo y reábrela: el progreso sigue ahí.

## Copia de seguridad

Menú «Nivel · XP» → **Exportar copia** → «Descargar archivo» genera
`vicks_kysats_backup_AAAA-MM-DD.json`. Se restaura con **Importar**. Recomendado una vez
por semana; la guía lo recuerda sola.

**Cada app tiene su propia copia**, porque cada una tiene su propio espacio de datos: si
usas varias, expórtalas por separado.

## Límites conocidos

- La versión online en claude.ai no admite service worker ni descargas: allí el backup se
  copia como texto o se comparte con «Compartir».
- La voz griega (🔊) depende de que el sistema tenga instalada una voz el-GR
  (iOS: Ajustes → Accesibilidad → Contenido hablado → Voces → Ελληνικά).
- Build de la app raíz: `44288203d1`.
