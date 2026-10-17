---
name: qc-loop
description: Bucle de control de calidad del video renderizado. Extrae frames a 10 fps, lanza los sub-agentes revisores y corrige hasta que pasen los 6 chequeos. Úsala antes de entregar o publicar un render.
---

# QC loop

Entrada: ruta del render (por defecto `out/draft_video.mp4`).

## Pasos
1. Extrae frames a **10 fps** (1 fps pasa por alto la mayoría de los errores). El comando es nuestro (las fuentes no lo muestran):
   ```bash
   mkdir -p pipeline/qc_frames && ffmpeg -y -i out/draft_video.mp4 -vf fps=10 pipeline/qc_frames/%05d.jpg
   ```
   Para ahorrar tokens, usa hojas de contacto (Jay E | RoboNuggets): `-vf "fps=10,tile=5x4"` y revisa por bloques.
2. Lanza los sub-agentes revisores (modelo Sonnet), cada uno con la ruta del render y de los frames:
   - `qc-visual-inspector`: los 6 errores críticos visuales.
   - `qc-voice-style`: texto y audio contra `claude.md` y `voice.md` del perfil activo.
   - `qc-fact-checker`: cifras, fechas y nombres contra `pipeline/transcript.json` y el perfil activo.
3. Si hay fallos: corrige solo el componente afectado en `src/graphics/` (re-render parcial del segmento, no del video entero), renderiza y repite desde el paso 1.
4. **Parada:** el bucle termina cuando pasan los 6 chequeos (criterio de Duncan Rogoff); entonces se entrega al usuario para revisión final.
   - Tope de seguridad **nuestro**: máximo 3 iteraciones; si persisten fallos, entrega el reporte con timestamps y pide ayuda. (Drake permite 1 reintento automático en su flujo de validación de datos; las fuentes no fijan un tope para el QC visual.)
5. Entrega un reporte: chequeos pasados, fallos corregidos, fallos pendientes (con timestamp).

## Prompt base del inspector (Duncan Rogoff, ~04:20)
```text
Check the video by looking at 10 frames every second and check for six different mistakes:
1. An animation that plays twice.
2. A graphic that flashes on screen for a split second.
3. Text that shows up too late for you to read it.
4. A graphic covering my face.
5. A word I said twice in a row.
6. My lips drifting out of sync with my voice.

When giving feedback or correcting a mistake, find the rule in the prompt/skill that would have stopped the mistake and rewrite that rule instead of stacking a new one on top.
```
Adicional nuestro: texto fuera de la zona segura 9:16 (ver `claude.md`).

## Ahorro de tokens y tiempo
- Opus solo para planificar; Sonnet para construir y revisar.
- Renders de revisión a media resolución; 4K solo tras la aprobación final.
- Motion blur desactivado durante las pruebas (render ~3x más rápido).
- Renders de sub-agentes en cola (uno por uno), no 6 a 9 en paralelo, para no saturar RAM/GPU.
- Re-render parcial del segmento modificado.
- Pide cambios con valores numéricos ("10% más grande", "desatura 50%").

## Aprendizaje
Si el usuario da feedback manual después, no solo arregles el proyecto: identifica la regla de `claude.md` (o de una skill) que falló o faltó y **reescríbela** (reemplaza, no acumules reglas).
```text
I finished making the edits to the video. Look at what I did and update your skill or prompt so next time you get me closer to the final version.
```
