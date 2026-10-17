---
name: higgsfield-budget
description: Control presupuestario ("anti credit trap") para cualquier generación de imagen o video con el conector Higgsfield MCP. Úsala antes de llamar a generate_image o generate_video.
---

# Higgsfield: control de presupuesto

Nunca llames a `generate_image` ni `generate_video` sin aprobación explícita del usuario.

## Antes de generar, pregunta y espera respuesta
1. Relación de aspecto (9:16 o 16:9).
2. Encuadre / duración del plano (close-up, medio, general).
3. Modelo a usar (ver tabla).
4. Muestra: saldo de créditos actual, costo estimado del render y **3 opciones de prompt**.

No llames a la herramienta hasta recibir confirmación explícita ("sí", "procede", etc.).

## Modelos (costos aproximados según los tutoriales; verificar en la plataforma)
| Uso | Modelo | Créditos aprox. |
|---|---|---|
| B-roll fotorrealista de alta calidad | Cling 3.0 / Seedance 2.0 Fast | 20 a 40 |
| Clips conceptuales económicos | Seedance 2.0 Mini | 10 a 20 |
| Imágenes estáticas con texto nítido | GPT Image 2 / Nano Banana Pro | verificar |
| Consistencia de personaje | Character Sheets / Soul Character | verificar |

## Reglas
- Usa primero assets propios (capturas, B-roll existente en `assets/`). Higgsfield solo para conceptos abstractos o que no existan.
- Genera solo los puntos del `pipeline/beatmap.md` marcados como B-roll IA.
- Si el saldo no alcanza para todos los puntos, propón cuáles priorizar.
