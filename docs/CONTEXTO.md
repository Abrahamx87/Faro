# Contexto del proyecto y guía de traspaso

Documento para cualquier persona o asistente de IA que continúe el trabajo en Faro. Léelo completo antes de tocar el repositorio y **actualiza el [registro de traspaso](#registro-de-traspaso) al terminar tu sesión**. Está pensado para que varias personas e IA trabajen en paralelo sin romper nada.

- Sitio publicado: https://abrahamx87.github.io/Faro/
- Repositorio: https://github.com/Abrahamx87/Faro (rama principal `main`, licencia MIT)
- Reglas de trabajo breves: [AGENTS.md](../AGENTS.md) · Aportes: [CONTRIBUTING.md](../CONTRIBUTING.md) · Seguridad: [SECURITY.md](../SECURITY.md)

## 1. Qué es Faro

Analizador **estático y local** de señales de phishing en archivos (PDF, HTML, texto plano y Office Open XML). Genera un reporte explicable en español: puntaje heurístico, señales con evidencia, enlaces desactivados, huella SHA-256 y exportación a JSON o PDF (impresión del navegador).

- **Contexto académico:** prototipo del Instituto Tecnológico de Morelia, Campus II, Ingeniería en Ciberseguridad, materia Desarrollo Sustentable. Se entrega al profesor; el equipo está en el [README](../README.md#equipo-y-contexto-académico).
- **Lo que promete y lo que no:** detecta indicadores; **no certifica que un archivo sea seguro**. El puntaje no es una probabilidad y los pesos no están calibrados con phishing real. Esta honestidad es parte de la calificación: no la debilites.
- **Dos ediciones con un solo motor:**
  - *Local:* `python -m faro serve` (servidor en `127.0.0.1`) y CLI `python -m faro analyze archivo`.
  - *Web:* el mismo `faro/engine.py` corre en el navegador con Pyodide (WebAssembly), publicado en GitHub Pages. Los archivos no salen del navegador.

## 2. Mapa del repositorio

| Ruta | Función |
| --- | --- |
| `faro/engine.py` | **Única fuente de reglas y puntuación.** Identificación de formato, analizadores y reporte |
| `faro/service.py`, `faro/worker.py` | Edición local: proceso separado, 15 s, 2 análisis concurrentes, límites POSIX |
| `faro/server.py`, `faro/__main__.py` | Servidor local (CSP, verificación de Host y Origin) y CLI |
| `faro/web/` | Interfaz: `index.html`, `app.js`, `styles.css`, `icon.svg` (sin dependencias externas) |
| `faro/samples/` | Tres demostraciones inofensivas (`legitimo.pdf`, `verificacion.html`, `contenido_disfrazado.pdf`) |
| `browser/transport.js`, `browser/worker.mjs` | Edición web: transporte y Web Worker con Pyodide |
| `scripts/build_web.py` | Construye `dist/` (interfaz + motor + pypdf + Pyodide); `dist/` no se versiona |
| `tests/` | `test_engine.py`, `test_server.py`, `test_rules_catalog.py` |
| `docs/` | `ARCHITECTURE.md`, `REGLAS.md` (catálogo), `VALIDATION.md`, `DEMO.md`, `reporte-ejemplo.json` |
| `.github/workflows/` | `tests.yml` (Linux y Windows × Python 3.10 y 3.12) y `pages.yml` (pruebas, compilación y despliegue) |

Flujo de un análisis: la interfaz envía los bytes (API local o Web Worker) → `analyze()` identifica el formato por contenido → el analizador registra reglas con `Findings.add()` (cada regla suma **una sola vez**) → reporte JSON (`schema_version` 1) → `app.js` lo dibuja. Detalle en [ARCHITECTURE.md](ARCHITECTURE.md).

## 3. Invariantes: nunca los rompas

1. **Privacidad.** No enviar archivos a servicios externos, no visitar enlaces extraídos, no guardar el contenido de entrada, no registrar contenido en logs. El historial del navegador es opcional y solo guarda resúmenes.
2. **`engine.py` es autocontenido.** Solo biblioteca estándar y `pypdf` (importado de forma perezosa). Sin imports de otros módulos de `faro`, sin `subprocess`, `resource` ni acceso a disco: la edición web lo empaqueta como `faro_engine.py` dentro de Pyodide.
3. **Una sola fuente de reglas.** Las reglas y pesos viven solo en `engine.py`; la web y la documentación las reflejan y una prueba las mantiene sincronizadas.
4. **CSP estricta.** Sin atributos `style=`, sin scripts en línea, sin CDN, fuentes ni recursos remotos. Todo estilo va en `styles.css`. La edición web añade solo `wasm-unsafe-eval`.
5. **Honestidad del resultado.** Un análisis incompleto se marca como parcial o no compatible; nunca presentes un puntaje bajo como garantía. Si no se pudo revisar algo, muestra el límite (`warn()`).
6. **Ejemplos inofensivos** con destinos `.invalid`. No subas malware, archivos privados, correos reales ni credenciales.
7. **Interfaz y explicaciones en español**, accesibles y con teclado. Respeta `prefers-reduced-motion`.
8. **`pypdf` fijado en 6.10.0** (`requirements.txt`, `pyproject.toml`, comprobación en `build_web.py`). Otra versión pasa las pruebas, pero la compilación web falla a propósito.

## 4. Si cambias X, toca también Y

| Si cambias… | Actualiza también |
| --- | --- |
| Una regla (`add()` en `engine.py`) | `ruleCatalog` en `faro/web/app.js`, la fila en `docs/REGLAS.md` y una prueba. `test_rules_catalog.py` falla si faltan o si los pesos no coinciden |
| Un límite (`MAX_*`, `PDF_TEXT_SECONDS`, 15 s) | Tabla de alcance del README, la tabla de "Cómo funciona" en `index.html`, `service.py` y `browser/transport.js` si aplica, y `VALIDATION.md` |
| Texto de `index.html` que `build_web.py` sustituye | La cadena correspondiente en `scripts/build_web.py`: deben coincidir exactamente o la sustitución falla **en silencio** |
| IDs o clases del HTML | `app.js` y `styles.css`: la interfaz depende de `getElementById` y de clases como `working`, `hidden` y `data-demo` |
| El contrato del reporte | `ARCHITECTURE.md`, `renderReport()` en `app.js`, `docs/reporte-ejemplo.json` y `schema_version` |
| Una muestra de demostración | `faro/samples/`, `allowed` en `server.py`, `SAMPLES` en `build_web.py`, `demos` en `transport.js`, los botones `data-demo` y las pruebas |
| Dependencias o versión de `pypdf` | `requirements.txt`, `pyproject.toml`, `build_web.py` (comprobación y `AVISOS.txt`) y los workflows |
| Archivos de `faro/**`, `browser/**`, `scripts/build_web.py`, `requirements.txt` o `package*.json` | Se redespliega Pages al fusionar. Un cambio solo de `docs/` o `tests/` no lo hace |

## 5. Flujo de trabajo (cómo continuar sin romper nada)

1. **Sincroniza y revisa:** `git checkout main && git pull`. Mira los PR abiertos y la sección [Trabajo en curso](#trabajo-en-curso). Si otra persona o IA toca los mismos archivos, coordina antes de empezar.
2. **Una tarea, una rama, un PR.** Nombre: `tipo/descripcion-corta` (`fix/`, `feat/`, `docs/`, `test/`, `ci/`). Nunca trabajes directo en `main`.
3. **Cambios pequeños y descritos.** Commits en español con prefijo convencional (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `build:`, `chore:`) y, si lo hizo una IA, su línea `Co-Authored-By`.
4. **Verifica antes del PR:**
   - Pruebas: `PYTHONPATH=. python -m unittest discover -s tests -v` (o `python -m unittest discover -s tests -v` tras `pip install -e .`).
   - Interfaz: `python -m faro serve`, prueba las tres demostraciones y un archivo propio en escritorio (≈1366 px) y móvil (≈390 px); sin errores de consola ni desbordamiento horizontal.
   - Edición web: `pip install -r requirements.txt`, `npm ci`, `npm run build:web` y sirve `dist/` con `python -m http.server 8765 --directory dist`.
5. **Abre el PR** con tres secciones: *Problema*, *Cambios* y *Cómo lo verifiqué* (di también qué **no** pudiste verificar).
6. **Espera la CI en verde.** Las pruebas corren en Linux y Windows con Python 3.10 y 3.12.
7. **Fusiona solo con aprobación explícita de Abraham** (squash). Tras fusionar, si tocaste archivos que redespliegan Pages, comprueba que el flujo "Publicar Faro web" termine con éxito y revisa el sitio en un navegador.
8. **Deja constancia:** añade una fila al registro de traspaso (puede ir en el mismo PR).

### Coordinación entre varias IA y personas

- Declara en [Trabajo en curso](#trabajo-en-curso) la rama y los archivos que vas a tocar, y quítalo al terminar.
- Si llegas segundo a un archivo, actualiza con `git fetch origin && git rebase origin/main`. Usa `--force-with-lease` solo en **tu propia** rama; jamás fuerces `main`.
- No cambies ajustes del repositorio (visibilidad, Pages, secretos, ramas protegidas), no borres ramas ajenas ni reescribas historial publicado.
- Si la decisión cambia el alcance, el diseño o lo que se promete en el README, **pregunta a Abraham**; no la asumas.
- Informa con precisión: qué verificaste, cómo y qué quedó sin comprobar. Prefiere "no pude verificar X" a suponerlo.

## 6. Trampas conocidas

- **`python -I` y `PYTHONPATH`:** el modo aislado ignora `PYTHONPATH`; para las pruebas usa `PYTHONPATH=.` sin `-I`.
- **Entornos sin acceso a PyPI:** puede haber otra versión de `pypdf` (p. ej. 6.17.0). Las pruebas pasan, pero `npm run build:web` se niega a compilar; úsalo solo con 6.10.0.
- **El motor en el navegador es más lento** que en local y se corta a los 15 s. El texto de PDF se lee con un presupuesto de 7 s (`PDF_TEXT_SECONDS`) y hasta 500 páginas; un PDF de 164 páginas tarda ≈5 s.
- **Caché de GitHub Pages:** el navegador puede conservar archivos unos 10 minutos. Para ver un despliegue nuevo, cierra la pestaña y recarga con Ctrl+F5.
- **Lectores web y secciones ocultas:** `WebFetch` y herramientas similares no ven las páginas con `hidden` (Historial, Cómo funciona, El proyecto). Verifica esas secciones en un navegador real.
- **Capturas de página completa:** la barra lateral y la barra inferior móvil son `fixed`; en una captura completa aparecen a media página. Es un artefacto, no un defecto.
- **GitHub desde sesiones de Claude Code:** `gh pr create` falla porque GraphQL está bloqueado. Usa la API REST: `gh api repos/Abrahamx87/Faro/pulls --method POST --input pr.json` y, para fusionar, `gh api repos/Abrahamx87/Faro/pulls/N/merge --method PUT -f merge_method=squash`.
- **Windows:** `worker.py` no aplica los límites POSIX de memoria y CPU; se conservan el tiempo y el proceso separado.
- **Convenciones de movimiento (revisión con el criterio de Emil Kowalski):** solo se animan `transform` y `opacity`; los efectos de hover con desplazamiento van dentro de `@media(hover:hover) and (pointer:fine)` (en el celular el hover se queda "pegado"); los botones tienen `:active` con `scale(.97)`; las entradas usan `var(--ease-out)` y `@starting-style` (toast y resultados); el scroll por JavaScript pasa por `scrollBehavior()` para respetar `prefers-reduced-motion`; con movimiento reducido el spinner y la barra de carga laten con `opacity` en lugar de congelarse. No pongas `style=` en línea (CSP).
- **Lecciones de bugs ya corregidos:** una regla basada solo en el nombre debe evaluarse **antes** de decodificar el contenido (si no, se omite en binarios); los textos planos (`.csv`, `.md`, `.json`…) no son discordancia de extensión; un tope fijo de páginas convertía documentos legítimos en "riesgo no determinado".

## 7. Estado actual

Al **2026-11-04**:

- **En producción:** edición web en GitHub Pages con portada visual, 20 reglas visibles, historial opcional y reporte imprimible. `main` coincide con lo desplegado.
- **Calidad:** 33 pruebas automatizadas; CI verde en Linux y Windows con Python 3.10 y 3.12.
- **Verificado a mano:** las tres demostraciones (0, 60 y 30 puntos), carga de un `.csv` inocuo (0 puntos), `factura.pdf.exe` binario (+40, medio) y una norma ISO 27002 en PDF de 164 páginas (completo, riesgo bajo, ≈4.6 s).
- **Sin verificar:** pruebas de usabilidad con personas; la edición web en navegadores móviles distintos de Chrome (p. ej. Safari); impresión en móvil; eficacia contra phishing real. No se ha medido precisión ni falsos positivos (ver [VALIDATION.md](VALIDATION.md)).

## 8. Próximos pasos sugeridos

No son compromisos; priorízalos con Abraham.

1. **Hasta terminar la presentación al profesor:** propuesta de congelamiento (confirmar con Abraham): solo correcciones de errores y documentación, sin refactors ni dependencias nuevas.
2. Calibrar pesos con un conjunto etiquetado y separar datos de ajuste y de evaluación (plan en [VALIDATION.md](VALIDATION.md)).
3. Pruebas de usabilidad con consentimiento, comparando decisiones con y sin Faro.
4. Cobertura adicional de Office (campos y fórmulas), análisis de adjuntos internos con presupuesto acumulado y OCR opcional.
5. Revisión de accesibilidad (contraste, lector de pantalla) y verificación en más navegadores móviles.

## 9. Lista de comprobación para la entrega

- [ ] Abrir https://abrahamx87.github.io/Faro/ y esperar "Motor listo en tu navegador".
- [ ] Las tres demostraciones muestran 0, 60 y 30 puntos; la portada se oculta al analizar y vuelve con "Nuevo análisis".
- [ ] Subir un archivo propio y exportar el reporte JSON y el PDF (Imprimir / PDF).
- [ ] El historial está desactivado por defecto y se borra con "Borrar historial".
- [ ] `main` sin PR abiertos a medias; CI en verde; README y este documento al día.
- [ ] Dejar claro en la exposición el alcance: detecta indicadores, no certifica seguridad.

## Trabajo en curso

Ninguno registrado. Antes de empezar, anota aquí: *fecha · quién (persona o IA) · rama · archivos que tocarás*, y bórralo al fusionar o abandonar la rama.

## Registro de traspaso

Agrega una fila **al final** por sesión de trabajo.

| Fecha | Quién | Qué se hizo | PR | Pendiente o aviso |
| --- | --- | --- | --- | --- |
| 2026-11-03 | Claude | Revisión inicial; corrección de falsos positivos de extensión y de la regla de doble extensión; catálogo de 20 reglas (`docs/REGLAS.md`) con prueba de sincronía | #1 | — |
| 2026-11-03 | Claude | Portada visual: hero con radar animado, cifras y pasos; se oculta durante el análisis | #2 | Edición web compilada solo verificada en CI y en el sitio publicado |
| 2026-11-04 | Claude | PDF largos: presupuesto de tiempo en vez del tope de 100 páginas (caso ISO 27002, 164 páginas) | #3 | Probar el mismo PDF en el celular tras recargar el sitio |
| 2026-11-04 | Claude | Este documento de contexto y su enlace desde `AGENTS.md` | #4 | Confirmar con Abraham el congelamiento previo a la entrega |
| 2026-11-05 | Claude | Pulido de movimiento: `:active` en botones, hover solo con mouse, tarjetas de pasos sin elevarse, entrada suave de toast y resultados, scroll del reinicio respeta movimiento reducido, spinner y barra con movimiento reducido, `pulse-dot` sin animar `box-shadow` | #5 | Revisar a mano en celular real tras el despliegue |
| 2026-11-08 | Claude | Pulido v2: `text-wrap` equilibrado en títulos, transiciones específicas y `:active` en demostraciones y pestañas, cifras tabulares, botón para pausar la animación del héroe (WCAG 2.2.2) | (este PR) | Revisar la vista previa antes de fusionar; sin cambios en el motor ni en las reglas |
