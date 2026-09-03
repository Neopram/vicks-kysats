# Vicks ΚΥΣΑΤΣ 2026 — versión instalable (PWA, sin conexión)

Esta carpeta contiene **la misma guía** (`index.html`, un solo archivo) más tres archivos que la hacen instalable y usable sin Internet:

| Archivo | Para qué |
|---|---|
| `index.html` | La guía completa (idéntica a `guia_kysats_2026.html`). |
| `manifest.json` | Nombre, icono y modo «pantalla completa» al instalarla. |
| `sw.js` | Service worker: guarda la guía en caché y la sirve sin conexión. |
| `icons/` | Iconos 180/192/512 px. |

El progreso se guarda en el propio dispositivo (IndexedDB + localStorage) tras cada respuesta. No hay servidor, cuentas ni envío de datos.

## Ya publicada: https://neopram.github.io/vicks-kysats/

Esta carpeta está subida al repositorio público `Neopram/vicks-kysats` y servida por GitHub Pages. En el iPhone: abre esa URL en **Safari** → Compartir → **Añadir a pantalla de inicio**. Para actualizarla, sube el nuevo `index.html` y `sw.js` al repositorio (o pídemelo: `gh` ya está autenticado).

## Opción A — Publicar gratis en GitHub Pages (cómo se hizo)

1. Crea una cuenta en github.com y un repositorio nuevo (por ejemplo `vicks-kysats`), público.
2. Sube **el contenido de esta carpeta** (no la carpeta entera): `index.html`, `manifest.json`, `sw.js` y la carpeta `icons/`. Se puede arrastrar y soltar en la web de GitHub («Add file → Upload files»).
3. En el repositorio: **Settings → Pages → Source: Deploy from a branch → Branch: main / (root) → Save**.
4. En 1–2 minutos la guía estará en `https://TU_USUARIO.github.io/vicks-kysats/`.
5. En el iPhone: abre esa URL en **Safari** → botón Compartir → **Añadir a pantalla de inicio**. A partir de ahí se abre como app, funciona sin conexión y Safari **no borra** sus datos a los 7 días (las apps instaladas están exentas).
6. Para actualizar la guía: sube el nuevo `index.html` y `sw.js`; la app se actualiza sola en la siguiente apertura con conexión.

## Opción B — Servidor local en tu ordenador

En esta carpeta ejecuta uno de estos comandos y abre `http://localhost:8080/`:

```
python -m http.server 8080
```
```
npx serve .
```

Sirve para probar la instalación y el modo offline en el portátil. Para el iPhone hace falta que ambos estén en la misma red y usar la IP del ordenador (`http://192.168.x.x:8080/`); el service worker solo se registra en `localhost` o en `https`, así que en el móvil la caché offline no se activará con esta opción: usa la opción A.

## Comprobar que funciona sin conexión

1. Abre la guía con conexión una vez (se cachea).
2. Activa el modo avión y vuelve a abrirla: debe cargar y mostrar el aviso «⚡ offline» en la barra superior.
3. Responde preguntas, cierra la app del todo y reábrela: el progreso sigue ahí.

## Copia de seguridad

Menú «Nivel · XP» → **Exportar copia** → «Descargar archivo» genera `vicks_kysats_backup_AAAA-MM-DD.json`. Se restaura con **Importar** (elige el archivo o pega el texto). Recomendado: una vez por semana; la guía lo recuerda sola.

## Límites conocidos

- La versión online en claude.ai no admite service worker ni descargas: allí el backup se copia como texto o se comparte con «Compartir».
- La voz griega (🔊) depende de que el sistema tenga instalada una voz el-GR (iOS: Ajustes → Accesibilidad → Contenido hablado → Voces → Ελληνικά).
- Build: `44288203d1`.
