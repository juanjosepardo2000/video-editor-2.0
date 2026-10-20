---
name: director-editorial
description: Decide qué mostrar, cuándo y con qué recurso en cada fragmento del video (criterio editorial profesional), siguiendo las reglas del perfil activo. Úsala al construir el beat map, antes de renderizar.
---

# Director editorial

Entrada: `pipeline/transcript.json` (video ya cortado), perfil activo (`profiles/ACTIVE`: `profile.json`, `style_guide.md`, `references.md`), contratos de `docs/contratos.md`.
Salida: un beat map **v2** (`# | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | B-roll | Zona | Transición | SFX | Caption`, encabezado `Contrato: v2`) y un **informe de decisiones** breve que explique por qué se eligió cada recurso.
Hasta que el lector de Gonzalo acepte v2, convierte a v1 con `python3 scripts/beatmap_v2_to_v1.py <v2.md> <v1.md>` para renderizar.

## 1. Segmentar en beats
- Un beat es una idea o frase con lo que se ve mientras se dice. Duración objetivo: `editing.sceneChangeSec` del perfil (perfil-1: 2 a 4 s); evita beats de menos de 1.4 s y de más de 5 s.
- Los límites deben caer **entre palabras** del transcript: `Fin` del beat >= fin de su última palabra e `Inicio` del siguiente <= inicio de su primera palabra, con **un decimal** (`mm:ss.s`); si el hueco entre dos palabras es menor de 0.1 s y no cabe uno, usa el punto medio con **dos decimales**. Los lectores aceptan de uno a tres decimales.
- `Speech` es el texto literal del transcript (misma ortografía y puntuación).

## 2. Clasificar el mensaje y elegir el recurso
| Lo que se dice | Etiqueta en `Visual` | Escena |
|---|---|---|
| Una cifra o porcentaje | `[contador]` o `[cifra]` | FULLSCREEN o CAPTION_UI |
| Antes/después, comparación, "vs" | `[comparacion]` | SPLIT |
| Afirmación fuerte, noticia, cita | `[titular]` | FULLSCREEN |
| Pregunta o búsqueda | `[busqueda]` | CAPTION_UI o FULLSCREEN |
| Pasos o enumeración | `[lista]` | CAPTION_UI |
| Concepto con título corto | `[tarjeta]` | CAPTION_UI |
| Frase clave de impacto | `[interludio]` | FULLSCREEN |
| Imagen de apoyo pequeña | `[recuadro]` | CAPTION_UI |
| Concepto abstracto o escenario que no se ve | `[broll]` | FULLSCREEN o SPLIT |
| Explicación normal | `[hablante]` | CAPTIONS |

`Visual` = `[etiqueta]` + instrucción interna de diseño (nunca se imprime). En la duda, elige `[hablante]`: menos es más.

## 3. Reglas del perfil que debes cumplir
Lee `profile.json` > `editing` y verifica al final:
- **Hook:** en el primer segundo debe haber texto grande o titular (palabra clave en `Caption`, o `Texto en pantalla` si la frase abre con una afirmación o pregunta).
- **Densidad:** `maxSimultaneousLayers` (1 en perfil-1: un solo gráfico llamativo a la vez), `minGapBetweenGraphicsSec` (separación mínima entre gráficos), `graphicsCoverageTarget` (porcentaje del tiempo con gráficos; ±10 puntos).
- **Variedad:** nunca la misma etiqueta más de 2 veces seguidas; alterna encuadre (usa `Transición: zoom-in` como punch-in sobre el hablante en tramos largos sin gráfico).
- **Subtítulos:** `captionWordsPerGroup`, `captionAnchorY`; una sola palabra clave por frase en `Caption` (1 a 3 palabras literales de `Speech`).
- **Rostro:** nunca decidas una posición que tape la cara. `Zona` es solo una preferencia (`arriba`, `abajo`, `lado`, `auto`); por defecto `auto`. En `SPLIT` el gráfico va `arriba`.

## 4. `Texto en pantalla`
Único copy visible en tarjetas y gráficos. Sale **solo** de lo dicho en `Speech` o del perfil activo; máximo 4 palabras (las listas, una por línea); cifras copiadas exactamente; `-` si no corresponde. Nunca inventes datos, nombres ni llamadas a la acción que no se digan.

## 5. B-roll (columna `B-roll`)
Orden: **material propio** (`own:archivo`, de `assets/`) → **Pexels** (`stock:palabras`) → **IA** (`ai:prompt`, solo si el perfil permite créditos y Juan aprueba el costo con `higgsfield-budget`).
- Úsalo para conceptos abstractos o escenarios que el hablante describe pero no se ven; respeta `broll.coverageTarget`.
- Palabras de búsqueda: 2 a 4 palabras **en inglés**, sustantivos concretos y visuales (por ejemplo `video editing software screen`), sin nombres propios ni marcas; ten un sinónimo de respaldo en el informe.
- El perfil `en construccion` con `maxAiCreditsPerVideo: 0` no usa IA.

## 6. SFX
`whoosh` en zooms y transiciones; `pop` al aparecer una tarjeta o recuadro; `hit` en el cierre o el clímax; `riser` solo si hay al menos 3 s antes del clímax; `-` en el resto. Nunca más de un SFX por beat salvo `whoosh, hit` en un clímax.

## 7. Informe de decisiones (obligatorio al presentar el beat map)
Tabla corta: beat → recurso elegido → motivo (una línea) y un bloque de comprobación: cobertura de gráficos (% real frente al objetivo), separación mínima, variedad de etiquetas, hook en el primer segundo, `Caption` literal, texto en pantalla sacado de lo dicho, B-roll y presupuesto. Si algo no se cumple, dilo y explica por qué.

## 8. Aprobación
El usuario aprueba el beat map antes de renderizar. Si el perfil está `en construccion`, indica qué reglas son provisionales (ver `style_guide.md`).
