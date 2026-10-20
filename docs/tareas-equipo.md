# Tareas del equipo: de prototipo a edición profesional

Basado en `docs/plan-mejoras.md` y `docs/guia-estilos-y-criterio.md`. Tamaño relativo: **S** (1 día), **M** (2 a 3 días), **L** (4 días o más). Prioridad: **P1** bloquea el resto, **P2** importante, **P3** después.

## Reglas de trabajo
- Una rama por tarea: `carlos/<id>` o `gonzalo/<id>`. Juan revisa y une a `main`; nadie sube directo a `main`.
- Toda tarea trae pruebas automáticas (`pytest` o `npm test`) que pasan en **Mac y Windows**. Scripts con `python3` en Mac y `python`/`py -3` en Windows.
- **Nada de medios en Git** (videos, audio, overlays, claves). Las claves van en `.env`.
- Cambiar un contrato (sección 5) exige avisar a los tres antes de programarlo.
- Antes de pedir revisión: ejecutar el flujo con `assets/raw/prueba.mp4` y adjuntar el resultado.

## 1. Carlos (backend, audio y análisis)

| ID | Tarea | Prior. | Tam. | Entrega | Se acepta cuando |
|---|---|---|---|---|---|
| **C1** | **Detector de rostro** `src/backend/face_tracker.py` (MediaPipe u OpenCV, solo CPU). Considerar la rotación del video (el de prueba es vertical con giro de 90°) | P1 | M | `pipeline/face_boxes.json` (contrato 5.1) y CLI `face_tracker.py video --out ...` | En `prueba.mp4` el rostro queda enmarcado en el 95% de los fotogramas muestreados; sin rostro devuelve lista vacía; procesa 30 s en menos de 60 s en un Mac sin GPU |
| **C2** | **Corte definitivo para videos largos**: lee `profile.json` (`silenceThresholdSec`, `cutPaddingMs`), regenera `transcript.json` con tiempos del corte, acepta `--cuts pipeline/cuts.json` (cortes semánticos de Claude, contrato 5.3) y `--model medium` | P1 | M | `rough_cutter.py` y `transcriber.py` actualizados | Un video de 60 a 90 s sale con tiempos correctos; los cortes de `cuts.json` se aplican; rellenos en español (`eh`, `em`, `ehm`) solo si se confirman en una prueba |
| **C3** | **Audio profesional** (`audio_mixer.py`): música que baja sola cuando hay voz (sidechain), voz normalizada, pico real <= -1 dBFS, SFX según el tipo de animación, microfundidos de 10 a 20 ms en los cortes, **pistas separadas** `voice.wav`, `music.wav`, `sfx.wav` además del mezclado | P1 | L | Mezclador nuevo + pruebas | La música baja al menos 8 dB bajo la voz; pico real <= -1 dBFS; tres pistas separadas que suman el mezclado; prueba automática de audibilidad de SFX |
| **C4** | **B-roll con Pexels** `src/backend/broll_search.py`: lee `stock:palabras` de la columna `B-roll` del beat map, consulta la API (vertical, duración >= la del beat), descarga a `pipeline/broll/`, guarda `pipeline/broll_credits.json`. Clave en `.env` (`PEXELS_API_KEY`); caché y manejo de límites | P2 | M | Módulo + pruebas con la API simulada | Descarga 3 clips para consultas distintas, registra autor y enlace, no vuelve a bajar lo ya descargado, nunca imprime la clave; revisa los términos de uso vigentes de Pexels y los anota en el README |
| **C5** | **`style_analyzer.py` v2**: densidad y tipos de SFX por minuto, presencia de música frente a voz, detección de cortes más fiable | P2 | M | Analizador actualizado | Sobre las 10 referencias entrega SFX por minuto; resultados guardados en `profiles/<perfil>/metrics/` |
| **C6** | **QC de medios** `qc_media.py`: pantallas negras, loudness y pico real, duración, resolución, sincronía de subtítulos con el transcript | P2 | M | `pipeline/qc_media.json` | Detecta una pantalla negra y un pico sobre 0 dBFS inyectados a propósito |
| **C7** | Orden y portabilidad: README con el flujo paso a paso, `requirements.txt` fijado, script para limpiar `pipeline/` y `out/`, compatibilidad Windows/Mac | P3 | S | README y scripts | Un equipo nuevo ejecuta el flujo siguiendo solo el README |

## 2. Gonzalo (gráficos, composición y CapCut)

| ID | Tarea | Prior. | Tam. | Entrega | Se acepta cuando |
|---|---|---|---|---|---|
| **G1** | **Compositor adaptativo**: con `face_boxes.json` calcula zonas libres (fuera del rostro y de las zonas seguras), mueve o reduce capas, suaviza el movimiento y respeta los campos de `profile.json`: `captionAnchorY`, `captionWordsPerGroup`, `graphicsMode`, `neverOverFace`, `maxSimultaneousLayers`, `minGapBetweenGraphicsSec` | P1 | L | Compositor en `src/graphics/` + pruebas | En el video de prueba ninguna capa toca el rostro (comprobado por G6); `SPLIT` pone el gráfico arriba y el hablante abajo; `FULLSCREEN` oculta de verdad al hablante |
| **G2** | **Revisar y unir `juan/integracion-e2e`** (columna `Texto en pantalla`) y corregir los 3 fallos: relleno vacío en tarjetas, posición de `CAPTION_UI`, contraste del acento en `corporativo-sobrio`; `validate_profiles.mjs` debe usar el beat map de ejemplo | P1 | M | PR aprobado | Pruebas en verde; la tarjeta de `CAPTION_UI` queda en el tercio inferior; contraste del texto >= 4.5:1 |
| **G3** | **Biblioteca de componentes según la rúbrica**: palabra clave con color y tamaño (con acento serif cursivo), recuadro pequeño de esquinas redondeadas, interludio de texto cinético, lista con píldoras numeradas, cifra grande; más los que ya hay (contador, titular, búsqueda, tarjeta) | P2 | L | Componentes con propiedades tipadas | Cada tipo de mensaje de la rúbrica tiene un componente y una prueba visual |
| **G4** | **Escenas con B-roll**: video de fondo vertical con recorte, oscurecido o desenfoque y movimiento suave, texto encima; lee `pipeline/broll/` y la columna `B-roll` | P2 | M | Componente `BrollScene` | Un beat con `stock:` o `own:` muestra el clip con texto legible |
| **G5** | **Capas nativas de CapCut**: ampliar `build_capcut_from_template.py` con subtítulos, zooms con fotogramas clave y pistas de audio separadas; requiere la plantilla maestra de Juan | P2 | L | Constructor ampliado | El proyecto abre en CapCut 9.4.0 sin avisos y los subtítulos y zooms son editables |
| **G6** | **QC de geometría** `qc_geometry.py`: con el recuadro real de cada capa del overlay y `face_boxes.json` calcula solape con el rostro, violaciones de zona segura, contraste y capas superpuestas | P1 | M | `pipeline/qc_geometry.json` | Detecta una tarjeta puesta sobre el rostro a propósito |
| **G7** | **Parser del beat map v2** (`sync-beatmap.mjs`): acepta v1 y v2 y las columnas `B-roll` y `Zona`; valida prefijos y valores; prueba con `pipeline/examples/beatmap.v2.example.md` | P1 | S | Parser actualizado | Lee el ejemplo v2 y el beat map v1 actual; rechaza `Zona` o `B-roll` inválidos con error claro |
| **G8** | Rendimiento y espacio: tiempos de render, no dejar archivos grandes sueltos en `out/` | P3 | S | Informe y limpieza | Render de 60 s en menos de 3 minutos en un Mac sin GPU |

## 3. Juan (decisiones y materiales)

| ID | Tarea | Para qué |
|---|---|---|
| J1 | Comentar los 10 videos de referencia (`references.md`) | Afinar el criterio de `perfil-1` |
| J2 | **Liberar espacio en el Mac** (hoy quedan unos 495 MB) | Poder renderizar y exportar |
| J3 | Clave gratuita de Pexels en `.env` | Habilita C4 |
| J4 | Plantilla maestra de CapCut con todas las pistas | Habilita G5 |
| J5 | 2 o 3 videos de prueba: uno con cifras y comparaciones, uno de 60 s o más, uno con otro encuadre | Validar H1 a H7 |
| J6 | Aprobar los contratos de la sección 5 | Desbloquea C1, C4, G1, G7 |
| J7 | Decidir plan de Higgsfield (hoy gratis, 10 créditos) | Respaldo de B-roll con IA |
| J8 | Elegir y aprobar el siguiente perfil o estilo | Probar que el sistema generaliza |

## 4. Claude (desde la sesión de Juan)
- **D1** Skill `director-editorial` con la rúbrica mensaje → recurso y las reglas de `perfil-1`.
- **D2** Skill `beatmap` v2 con columnas `B-roll` y `Zona`, hook en el primer segundo y variedad de encuadre.
- **D3** Corrección de la transcripción y cortes semánticos en `pipeline/cuts.json`.
- **D4** Planificador de B-roll: palabras de búsqueda, elección entre candidatos y respaldo con Higgsfield dentro del presupuesto.
- **D5** Control de calidad ampliado (`qc-loop`) y el comando único `editar-video`.
- **D6** Revisión y unión de las ramas del equipo.

## 5. Contratos
1. `pipeline/face_boxes.json`: `{fps, width, height, frames:[{t, boxes:[{x, y, w, h, conf}]}]}`; coordenadas de 0 a 1 respecto al video **ya rotado**; muestreo a 10 fps y suavizado.
2. **Beat map v2 (aprobado por Juan).** Columnas nuevas después de `Texto en pantalla`: **`B-roll`** (`-`, `own:archivo`, `stock:palabras`, `ai:prompt`) y **`Zona`** (`arriba`, `abajo`, `lado`, `auto`; es una preferencia, el compositor decide). Orden completo: `# | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | B-roll | Zona | Transición | SFX | Caption`.
   - **Versión:** línea `Contrato: v2` en el encabezado del archivo.
   - **Transición:** los lectores aceptan **v1 y v2**; sin `B-roll` se asume `-` y sin `Zona`, `auto`. Se retira v1 cuando los tres hayan migrado.
   - **Validación:** `B-roll` solo con prefijos `own:`, `stock:` o `ai:`; `Zona` solo con los 4 valores; errores claros.
   - **Archivo de ejemplo:** `pipeline/examples/beatmap.v2.example.md` (el beat map real sigue en v1 hasta que migren los lectores).
   - **Estado de los lectores:** exportador de CapCut y mezclador de Carlos ya aceptan v2 (probado); **falta el lector de Gonzalo** (`sync-beatmap.mjs`, tarea G7).
3. `pipeline/cuts.json`: `[{start, end, reason}]` en tiempos del video original, en segundos.
4. `profile.json`: campos de `editing` y `broll` ya definidos en `perfil-1`.
5. `pipeline/qc_media.json`, `pipeline/qc_geometry.json` y el informe final `pipeline/qc_report.json`.

## 6. Orden recomendado y dependencias
```text
Semana 1:  C1 (rostro)  ->  G1 (compositor)      | G2 (revisión y fallos) | C2 (corte largo) | J2, J3, J5, J6
Semana 2:  C3 (audio)   |  G6 (QC geometría)     | C4 (Pexels)  -> G4 (B-roll) | D1, D2
Semana 3:  G3 (componentes) | G7 (parser) | C5, C6 | D3, D4
Semana 4:  G5 (CapCut nativo, necesita J4) | prueba final de 60 a 90 s con 2 perfiles | D5
```
G1 depende de C1 y del contrato 5.1; G4 depende de C4; G5 depende de J4; G7 ya no espera a J6 (contrato aprobado) y desbloquea a D2 y a G4.

## 7. Mensajes listos para sus asistentes de código
**Carlos:** «Lee `docs/tareas-equipo.md`, `docs/guia-estilos-y-criterio.md` y `profiles/perfil-1/`. Empieza por C1 (detector de rostro) en la rama `carlos/c1-face-tracker`. Antes de programar muéstrame el plan, la librería elegida y cómo manejarás la rotación del video. No subas medios ni claves. Entrega pruebas que pasen en Mac y Windows.»
**Gonzalo:** «Lee `docs/tareas-equipo.md` y `docs/guia-estilos-y-criterio.md`. Empieza por G2 (revisar `juan/integracion-e2e` y corregir los 3 fallos) y luego G1 (compositor adaptativo) en la rama `gonzalo/g1-compositor`, a partir del contrato `face_boxes.json`. Antes de programar muéstrame el algoritmo de zonas libres y cómo suavizarás el movimiento. No toques `profiles/` ni `src/backend/`.»
