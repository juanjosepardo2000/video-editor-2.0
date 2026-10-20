# Guía 2: criterio y estilos de edición

Arranca por el **criterio**: antes de mejorar gráficos o audio, el sistema necesita saber *qué es una buena edición* en cada estilo. Esta guía convierte videos de referencia en reglas medibles que se guardan en un **perfil**. El plan técnico completo está en `docs/plan-mejoras.md`.

## 1. Principios
- **Un perfil = un estilo.** El primero es `profiles/perfil-1/` (estado: *en construcción*).
- **Antes de editar cualquier video, Claude pregunta qué estilo usar** (skill `editar-video`) y avisa si el perfil aún no está calibrado.
- **Se imita la técnica, no el video.** Las referencias solo aportan enlaces y métricas; los archivos no se suben al repo.
- **Regla con respaldo:** cada regla del perfil debe indicar de qué referencias sale. Sin respaldo, queda marcada como provisional.

## 1b. Todo perfil tiene dos bloques de referencias
| Bloque | Qué aprende | Referencias mínimas |
|---|---|---|
| **Narrativo** | Ritmo, hooks, cortes, reacciones y selección de momentos | 5 videos de un creador o de creadores similares |
| **Visual** | Subtítulos, tarjetas, zooms, SFX y composición 9:16 | 5 videos de edición gráfica profesional |

Un perfil nuevo **no se da por calibrado** hasta tener ambos bloques. Al crearlo, el sistema pide los videos de cada bloque (enlace o archivo), qué le gusta al usuario y qué no copiar. Ejemplo ya hecho: `perfil-1` (narrativo: carpeta «DavoXeneizze»; visual: carpeta «Videos Profesionales»).

## 2. Flujo para calibrar un perfil

| # | Paso | Responsable | Resultado |
|---|---|---|---|
| 1 | Reunir 10 a 30 videos de **un mismo estilo** (mejor 9:16) | Gonzalo, Carlos y Juan | Filas en `profiles/perfil-1/references.md` |
| 2 | Medir cada video | Carlos (`style_analyzer.py`) | `profiles/perfil-1/metrics/<n>.json` |
| 3 | Observar fotogramas muestreados con la rúbrica (sección 3) | Claude | Notas cualitativas por video |
| 4 | Sintetizar reglas medibles | Claude | `style_guide.md` y `profile.json` actualizados |
| 5 | Editar un clip de prueba en ese estilo y compararlo lado a lado con las referencias | Claude y Gonzalo | Clip de validación |
| 6 | Aprobar y congelar | Juan | `status: calibrado`, `version` +1 |

## 3. Rúbrica de observación (qué se mide y qué se mira)
**Medible por código (Carlos):** duración de planos (detección de cortes), pausas y silencios, palabras por minuto, nivel de música y voz, densidad de efectos de sonido por minuto.
**Observable por Claude en fotogramas:** frecuencia y tipo de gráficos y su posición, tamaño y estilo de subtítulos, uso de zooms y transiciones, paleta y tipografía, hook de los primeros 3 s, cierre, uso de B-roll (tipo, fuente, % del tiempo).

## 4. Cómo elegir buenas referencias
- Un solo estilo por perfil; si dudas, es otro perfil.
- Misma plataforma y formato que el objetivo (Reels, TikTok, Shorts, vertical).
- Duración parecida a lo que se va a producir.
- Incluye variedad de creadores para no copiar a uno solo.
- Cada integrante aporta al menos 3 y escribe **qué le gusta** y **qué no copiar** (marcas, música, voz, contenido).

## 5. B-roll según el estilo (Pexels e Higgsfield)
Cada perfil define su política en `profile.json` > `broll`:
- **Orden:** material propio, luego **Pexels** (stock gratuito, vertical), luego **Higgsfield** (IA, de pago).
- **Pexels:** revisar sus términos vigentes (uso comercial y atribución); guardar `pipeline/broll_credits.json`; la clave va solo en `.env`.
- **Higgsfield:** solo si ningún candidato de Pexels sirve y el perfil permite créditos (`maxAiCreditsPerVideo` > 0), siempre con la skill `higgsfield-budget`. Tu cuenta gratuita tiene 10 créditos: no alcanza para video.
- El estilo decide *cuánto* B-roll: un perfil viral puede usar más; uno corporativo, casi nada.

## 6. Lo que hace falta para un resultado excelente (resumen)
1. **Criterio por estilo** (esta guía): reglas medibles con respaldo.
2. **Composición adaptativa:** detección de rostro y colocación de capas sin taparlo.
3. **Audio profesional:** música que baja sola con voz, voz normalizada, pistas separadas.
4. **Control de calidad automático** con informe y MP4 de revisión.
5. **CapCut con capas nativas** (subtítulos, zooms, audio) y plantilla maestra.
6. **B-roll sin copyright** integrado (Pexels) con respaldo de IA.

## 7. Encargos de este tramo
**Gonzalo y Carlos:** cada uno aporta al menos 3 referencias en `references.md` (enlace, qué le gusta, qué no copiar). Carlos además entrega `style_analyzer.py`.
**Gonzalo:** revisar que los parámetros nuevos de `profile.json` (`maxSimultaneousLayers`, `minGapBetweenGraphicsSec`, `graphicsCoverageTarget`, `captionFontScale`, `broll`) no rompan su lector y, si hace falta, usarlos.
**Juan:** aportar sus referencias, definir el nombre y la idea del estilo de `perfil-1` cuando haya 10 videos, y aprobar la validación.
**Claude:** observar, sintetizar y escribir las reglas; mantener la pregunta de estilo antes de editar.

## 8. Cuándo se da el tramo por terminado
- [ ] `perfil-1` tiene al menos 10 referencias registradas y analizadas.
- [ ] `style_guide.md` y `profile.json` tienen reglas medibles con referencias de respaldo.
- [ ] Un clip de validación fue aprobado por Juan y el perfil pasa a `calibrado`.
- [ ] Al pedir editar un video, Claude pregunta el estilo y lo registra en `profiles/ACTIVE`.
