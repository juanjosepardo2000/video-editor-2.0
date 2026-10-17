# ai-video-editor

Sistema híbrido de edición de video: transcripción y cortes con Python/FFmpeg, gráficos con Remotion y exportación a un NLE (CapCut).

## Arquitectura (3 módulos)

| Módulo | Responsable | Carpeta | Función |
|---|---|---|---|
| Backend / Audio | **Carlos** | `src/backend/` | Transcripción (WhisperX), rough cut con FFmpeg, mezcla de SFX y música |
| Orquestación / BeatMap | **Juan** | `pipeline/` | Define el mapa de ritmo por escenas y coordina el flujo entre módulos |
| Graphics / NLE | **Gonzalo** | `src/graphics/`, `src/nle_bridge/` | Gráficos animados en Remotion y exportación de proyectos CapCut |

## Requisitos
- Python 3.10+, FFmpeg instalado, Node.js 18+

```bash
pip install -r requirements.txt
npm install
```

## Pipeline paso a paso
1. Colocar el video fuente en `assets/raw/`.
2. **Transcribir** → genera `pipeline/transcript.json` (timestamps por palabra):
   `python src/backend/transcriber.py assets/raw/video.mp4`
3. **Rough cut** → corta silencios/muletillas según el transcript:
   `python src/backend/rough_cutter.py assets/raw/video.mp4`
4. **BeatMap** → editar `pipeline/beatmap.md` con el ritmo por escena.
5. **Mezcla de audio** → SFX y música a -20/-23 dB:
   `python src/backend/audio_mixer.py`
6. **Gráficos** → previsualizar/renderizar con Remotion: `npm run studio` / `npm run render`
7. **Exportar a CapCut**: `python src/nle_bridge/capcut_exporter.py`
8. Resultados en `out/`.

Reglas de estilo: ver [claude.md](claude.md).
