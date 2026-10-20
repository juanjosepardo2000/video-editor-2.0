# Contratos entre piezas (fuente única)

Estado: **aprobado por Juan el 2026-10-19**. Si un contrato cambia, se avisa a los tres antes de programar. Coordenadas siempre **normalizadas de 0 a 1** respecto al video **ya rotado** (origen arriba a la izquierda). Tiempos en segundos del video **ya cortado**, salvo que se indique.

## 1. `pipeline/face_boxes.json` (C1 → G1, G6)
```json
{"fps": 10, "width": 720, "height": 1280, "source": "rough_cut.mp4",
 "frames": [{"t": 0.0, "boxes": [{"x": 0.31, "y": 0.18, "w": 0.34, "h": 0.22, "conf": 0.97}]}]}
```
- Muestreo a 10 fps, suavizado temporal, `boxes` vacío si no hay rostro; varios rostros = varias cajas.
- La caja incluye margen de seguridad de 10% alrededor del rostro (el compositor no lo agrega de nuevo).

## 2. Beat map v2 (J → G, C)
Definido en `pipeline/examples/beatmap.v2.example.md`. Aceptar v1 y v2.

### 2.1 Vocabulario de `Visual` (resuelve la relación recurso ↔ escena)
`Visual` empieza con una **etiqueta controlada** entre corchetes y sigue con texto libre (que nunca se imprime):
`[contador]`, `[comparacion]`, `[titular]`, `[busqueda]`, `[lista]`, `[cifra]`, `[tarjeta]`, `[interludio]`, `[recuadro]`, `[hablante]`, `[broll]`.
Ejemplo: `[comparacion] Antes y después de aplicar el método`. Sin etiqueta, el lector usa las pistas de texto actuales como respaldo.

| Etiqueta | Cuándo | Escena habitual |
|---|---|---|
| `[contador]` | Una cifra o porcentaje | FULLSCREEN o CAPTION_UI |
| `[cifra]` | Un número grande suelto | FULLSCREEN |
| `[comparacion]` | Antes/después, vs | SPLIT |
| `[titular]` | Noticia, cita, afirmación fuerte | FULLSCREEN |
| `[busqueda]` | Pregunta o búsqueda | CAPTION_UI o FULLSCREEN |
| `[lista]` | Pasos o enumeración | CAPTION_UI |
| `[tarjeta]` | Concepto con título corto | CAPTION_UI |
| `[interludio]` | Frase clave en texto cinético | FULLSCREEN |
| `[recuadro]` | Imagen pequeña de apoyo (esquinas redondeadas) | CAPTION_UI |
| `[hablante]` | Solo hablante y subtítulos | CAPTIONS |
| `[broll]` | Video de apoyo | FULLSCREEN o SPLIT |

## 3. `pipeline/cuts.json` (Claude → C2)
`[{"start": 12.4, "end": 13.1, "reason": "toma falsa: reinicio de frase"}]`, en tiempos del video **original**; no se solapan.

## 4. `pipeline/layout.json` (G1 → G6) y cajas de capas
```json
{"fps": 30, "width": 1080, "height": 1920, "profile": "perfil-1",
 "layers": [{"beat": 2, "kind": "tarjeta", "startFrame": 96, "endFrame": 249,
             "box": {"x": 0.08, "y": 0.66, "w": 0.84, "h": 0.2}, "textColor": "#1D1D1F", "backgroundColor": "#F5F5F7",
             "keyframes": []}]}
```
- `box` en coordenadas de 0 a 1 del lienzo de 1080×1920; `keyframes` opcional `[{frame, box}]` si la capa se mueve.
- G6 comprueba además la verdad del renderizado: calcula el rectángulo no transparente de cada fotograma del overlay y lo compara con `layout.json`. Las diferencias de más de 2% se reportan.

## 5. Informes de QC (C6, G6 → qc-loop)
Mismo esquema para `pipeline/qc_media.json` y `pipeline/qc_geometry.json`:
```json
{"generated": "2026-10-19T12:00:00", "video": "out/entrega/video.mp4",
 "checks": [{"id": "face_overlap", "status": "pass|warn|fail", "detail": "texto", "timestamps": [3.2, 3.3], "value": 0.0, "limit": 0.0}],
 "summary": {"pass": 0, "warn": 0, "fail": 0}}
```
Ids mínimos: **media:** `black_frames`, `loudness_lufs`, `true_peak`, `duration`, `resolution`, `subtitle_sync`. **geometría:** `face_overlap`, `safe_zone`, `contrast`, `simultaneous_layers`, `layout_vs_render`. El informe final `pipeline/qc_report.json` los une y añade las observaciones de Claude.

## 6. Audio (C3)
Carpeta `pipeline/audio/`: `voice.wav`, `music.wav`, `sfx.wav`, `mix.wav`; **48 kHz, 24 bits, estéreo, misma duración que el video y alineados en t=0**. Más `audio_report.json`:
`{"mix_lufs": -14.2, "true_peak_dbfs": -1.3, "music_below_voice_db": 9.1, "ducking_max_db": 12, "sfx_count": 4}`.
Objetivos: mezcla -14 LUFS (±1), pico real <= -1 dBFS, música al menos 8 dB por debajo de la voz mientras hay habla.

## 7. `pipeline/broll_credits.json` (C4)
```json
[{"beat": 3, "query": "video editing software screen", "pexels_id": 123, "url": "https://www.pexels.com/video/...",
  "author": "Nombre", "author_url": "https://www.pexels.com/@...", "file": "pipeline/broll/3_123.mp4",
  "duration_s": 12.0, "width": 1080, "height": 1920, "license": "Pexels License", "downloaded_at": "2026-10-19"}]
```

## 8. Métricas de estilo (C5)
Esquema actual de `style_analyzer.py` más bloques nuevos, compatibles hacia atrás:
- `sfx`: `{"count": 0, "per_minute": 0.0, "events": [{"t": 3.2, "duration_s": 0.4, "kind": "whoosh|pop|click|hit|riser|other", "conf": 0.6}]}`. El tipo es una **clasificación aproximada**: si no hay confianza suficiente, `kind: "other"`.
- `music_voice`: `{"music_present_percent": 0, "voice_present_percent": 0}`.
- **Dónde se guardan:** el análisis escribe en `profiles/<perfil>/metrics/`. Excepción a la regla «no tocar profiles/»: **Carlos puede añadir archivos solo en esa subcarpeta**; Juan o Claude revisan antes de unir.

## 9. Informe de rendimiento (G8)
`pipeline/perf_report.json`: `{"video_s": 60, "render_s": 150, "ratio": 2.5, "machine": "Mac arm64 CPU", "frames": 1800, "disk_used_mb": 140}`.

## 10. Campos de perfil (`profile.json` > `editing`)
`silenceThresholdSec`, `keepPauseSec` (pausa que se **conserva** al cortar un silencio largo, para ritmo natural; `perfil-1`: 0.3), `cutPaddingMs`, `sceneChangeSec`, `captionAnchorY`, `captionWordsPerGroup`, `graphicsMode`, `neverOverFace`, `maxSimultaneousLayers`, `minGapBetweenGraphicsSec`, `graphicsCoverageTarget`, `captionFontScale`.
**Regla de corte (resuelve «pausas naturales» frente a 0.5 s):** se eliminan los silencios mayores que `silenceThresholdSec`, pero se conserva `keepPauseSec` de cada uno.

## 11. Portabilidad Python (Mac/Windows)
El envoltorio que elige `python3`, `python` o `py -3` (el primero disponible) vive en **`src/nle_bridge/run_python.mjs`** (decisión del 2026-10-19: el alcance de Gonzalo no incluye `scripts/`, que es de Juan y Claude). `package.json` lo usa; los scripts de Python de Carlos no lo necesitan.

## 12. Conjunto de desarrollo pareado (`pipeline/examples/`)
`pipeline/transcript.json`, `face_boxes.json` y los videos son **artefactos locales de cada persona** (Git los ignora): nunca se mezclan con un beat map ajeno. Para desarrollar y probar todos usan el mismo conjunto pareado, versionado:
- `pipeline/beatmap.md` (v1) y `pipeline/examples/beatmap.v2.example.md` / `beatmap.perfil1.propuesta.v2.md` (v2)
- `pipeline/examples/transcript.prueba.json`: transcript del **mismo** video que `pipeline/beatmap.md` (`prueba.mp4` de Juan, 16.1 s)
- `pipeline/examples/face_boxes.fixture.json`: rostro **sintético** (no detectado) para que G1 y G6 arranquen sin esperar a C1
Ejemplo: `npm run sync:beatmap -- --beatmap=pipeline/beatmap.md --transcript=pipeline/examples/transcript.prueba.json`.
