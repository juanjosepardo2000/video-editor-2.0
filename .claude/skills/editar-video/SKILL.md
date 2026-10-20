---
name: editar-video
description: Punto de entrada para editar un video. SIEMPRE pregunta primero qué estilo (perfil) usar, luego ejecuta el flujo con puntos de aprobación. Úsala cada vez que el usuario pida editar un video.
---

# Editar un video

## Paso 0: preguntar el estilo (obligatorio, antes de tocar el video)
1. Lista los perfiles: carpetas de `profiles/` sin `_template`, leyendo de cada `profile.json` el `name`, `description` y `status`.
2. Pregunta al usuario con `AskUserQuestion` cuál estilo quiere (máximo 4 opciones; si hay más, ofrece los más recientes y deja "Otro"). En cada opción indica el estado: `calibrado` o `en construcción`.
3. Si elige un perfil `en construcción`, avísale que sus reglas aún son provisionales (se calibran con los videos de `references.md`) y confirma que quiere seguir.
4. Escribe el nombre elegido en `profiles/ACTIVE` y léelo de ahí durante todo el flujo.
5. No asumas el estilo ni reutilices el de la vez anterior sin preguntar.

## Paso 1: confirmar el video
Ruta en `assets/raw/`, duración y orientación (revisa la rotación con `ffprobe`; un video vertical puede venir como 1280x720 con giro de 90°).

## Paso 2: flujo (cada punto con aprobación del usuario donde se indica)
1. Transcribir y cortar (backend de Carlos; `.venv/bin/python src/backend/transcriber.py` y `rough_cutter.py`). Muestra qué se quitó. **Aprobación.**
2. Corregir la transcripción solo con certeza (errores evidentes); nunca inventar palabras.
3. Beat map con la skill `beatmap` aplicando las reglas del perfil activo (`profile.json` > `editing` y `style_guide.md`). **Aprobación.**
4. B-roll (ver abajo).
5. Mezcla de audio, overlay y vista previa compuesta.
6. Control de calidad con la skill `qc-loop`.
7. Proyecto de CapCut (`build_capcut_from_template.py` e `install_capcut_draft.py`; medios en `~/Movies/editor-ia`).

## B-roll: política según el perfil (`profile.json` > `broll`)
Orden de preferencia, sin saltarse pasos: **1) material propio** de `assets/`, **2) Pexels** (stock gratuito, vertical), **3) Higgsfield** (de pago).
- Pexels: guarda los créditos en `pipeline/broll_credits.json` y no uses la clave fuera de `.env`.
- Higgsfield: solo si ningún candidato de Pexels sirve y `maxAiCreditsPerVideo` es mayor que 0; sigue siempre la skill `higgsfield-budget` (pedir aprobación del costo antes de generar).
- Marca en el beat map los beats con B-roll (`B-ROLL IA:` en `Visual`, o la columna `B-roll` cuando exista).

## Reglas
- Respeta la regla absoluta de `claude.md` (no inventar datos) y las zonas seguras.
- Si el perfil tiene `status: en construccion`, registra en el informe final qué reglas fueron provisionales.
