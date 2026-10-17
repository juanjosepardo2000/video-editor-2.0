---
name: qc-loop
description: Bucle de control de calidad del video renderizado. Extrae frames a 10 fps, lanza los sub-agentes revisores en paralelo y corrige hasta que pasen los 6 chequeos. Úsala antes de entregar o publicar un render.
---

# QC loop

Entrada: ruta del render (por defecto `out/draft_video.mp4`).

## Pasos
1. Extrae frames a **10 fps** (1 fps pasa por alto la mayoría de los errores):
   ```bash
   mkdir -p pipeline/qc_frames && ffmpeg -y -i out/draft_video.mp4 -vf fps=10 pipeline/qc_frames/%05d.jpg
   ```
   Para ahorrar tokens, agrupa los frames en hojas de contacto (`-vf "fps=10,tile=5x4"`) y revisa por bloques.
2. Lanza en paralelo los 3 sub-agentes (modelo Sonnet), cada uno con la ruta del render y de los frames:
   - `qc-visual-inspector`: los 6 errores críticos visuales.
   - `qc-voice-style`: texto y audio contra `claude.md` y `context/voice.md`.
   - `qc-fact-checker`: cifras, fechas y nombres contra `pipeline/transcript.json` y `context/`.
3. Si hay fallos: corrige el componente en `src/graphics/` (o el beat map), vuelve a renderizar y repite desde el paso 1.
4. Máximo 3 iteraciones. Si persisten fallos, entrega el reporte al usuario y pide ayuda.
5. Entrega un reporte: chequeos pasados, fallos corregidos, fallos pendientes (con timestamp).

## Los 6 errores críticos
1. Animación duplicada (se ejecuta dos veces seguidas).
2. Destello o parpadeo de 1 fotograma.
3. Texto ilegible por velocidad.
4. Gráfico cubriendo la cara del hablante.
5. Palabras o tomas repetidas no cortadas.
6. Desincronización de labios.

Más: texto fuera de la zona segura 9:16 (ver `claude.md`).

## Aprendizaje
Si el usuario da feedback manual después, no solo arregles el proyecto: identifica la regla de `claude.md` (o de una skill) que falló o faltó y **reescríbela** (reemplaza, no acumules reglas).
