---
name: higgsfield-budget
description: Control presupuestario ("anti credit trap") para cualquier generación de imagen o video con el conector Higgsfield MCP. Úsala antes de llamar a generate_image o generate_video, y para crear character sheets.
---

# Higgsfield: control de presupuesto

Nunca llames a `generate_image` ni `generate_video` sin aprobación explícita del usuario.

## Antes de generar, pregunta y espera respuesta
1. Imagen de referencia y encuadre / duración del plano (close-up, medio, general).
2. Relación de aspecto (9:16 o 16:9).
3. Estilo visual / vibra.
4. Modelo a usar (ver tabla; recomienda con base en el uso).
5. Muestra **3 opciones de prompt** en texto para que el usuario elija.
6. Muestra el saldo de créditos actual y el costo estimado del render.

No llames a la herramienta hasta recibir confirmación explícita ("sí", "procede", etc.).

## Modelos (costos aproximados de los tutoriales; verificar en la cuenta)
| Uso | Modelo | Créditos aprox. |
|---|---|---|
| B-roll cinematográfico fotorrealista | Kling 3.0 ("Cling 3.0") | ~20 por 10 s en 16:9 |
| Clips conceptuales rápidos | Seedance 2.0 Fast / Mini | ~20 a 40 por 15 s |
| Consistencia de personaje / estilo cinematográfico | Soul, Cinema Studio | verificar |
| Detalle preciso en mapas u objetos | MiniMax H3 | verificar |
| Imágenes con texto nítido | GPT Image 2 | verificar |
| Imágenes estáticas de alta calidad | Nano Banana Pro / 2 | verificar |

Referencia global: un video de 3 min (46 imágenes, 3 miniaturas, 2 character sheets) costó ~241 créditos (~$9.50 con un plan de 1,000 créditos por $39/mes).
Nota: dos fuentes dieron rangos distintos para Seedance (10 a 20 vs 20 a 40); confía en el saldo y la estimación que muestra el conector.

## Qué generar y qué no
- Higgsfield: B-roll fotorrealista, renders 3D abstractos, hojas de personaje y avatares IA.
- Assets propios: capturas de pantalla e interfaces reales, grabación del hablante, música y SFX de `assets/`.
- Genera solo los beats del `pipeline/beatmap.md` cuya columna Visual empiece con `B-ROLL IA:`.
- Si el saldo no alcanza para todos, propón cuáles priorizar.

## Subir archivos locales
Subir archivos desde el sandbox falla por restricciones de red. Usa el widget oficial `media_upload` o los IDs/UUIDs de assets ya subidos.

## Consistencia de personaje (character sheet)
1. Antes de generar el resto, pide: "Generate all the images for our video using the script timestamps, but FIRST generate a character reference sheet for approval".
2. Genera 2 o más variantes (Sheet A / Sheet B) con distintos ángulos.
3. Espera la aprobación explícita ("Sheet A is approved. Proceed to the other images").
4. Usa la hoja aprobada como referencia en cada escena para mantener luz, ropa y rasgos.
5. Con Higgsfield Soul, incluye el `UUID` del avatar en el prompt.
