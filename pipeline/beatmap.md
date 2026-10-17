# BeatMap

> Contrato entre Juan (lo escribe), Gonzalo (lee `Escena`, `Visual`, `Transición`, `Caption`) y Carlos (lee `SFX`).
> No cambies los nombres de columna ni los códigos de escena sin avisar a los tres.

## Configuración global
- Tema: light Apple
- Color de acento: orange
- Fuente principal: Inter Semibold
- Fuente de acento (script): TODO
- Colores de texto: TODO (principal / secundario)
- Formato: 9:16, 1080x1920, 30 fps
- Música: `assets/music/TODO.mp3` a -22 dB

## Códigos de escena
| Código | Significado |
|---|---|
| `CAPTIONS` | Hablante a pantalla completa + subtítulos |
| `CAPTION_UI` | Hablante + animación pequeña en el tercio inferior |
| `SPLIT` | Animación en la mitad superior, hablante en la inferior |
| `FULLSCREEN` | Animación al 100%, reemplaza al hablante |

## Beats
Tiempos en segundos sobre el video **ya cortado** (`mm:ss.s`). SFX: `tipo` o `tipo:archivo.wav`; `-` si no lleva.

| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 00:02.5 | (frase del hook) | CAPTIONS | Hablante, sin gráficos | - | riser | palabra clave en acento |
| 2 | 00:02.5 | 00:05.0 | "tres errores que arruinan tus edits" | CAPTION_UI | Tarjeta con 3 círculos numerados | slide-up | pop | números en acento |
| 3 | 00:05.0 | 00:08.0 | "haz cada elemento 25% más pequeño" | SPLIT | Icono que se reduce (arriba) | - | whoosh | - |
| 4 | 00:08.0 | 00:11.0 | (concepto complejo) | FULLSCREEN | Diagrama a pantalla completa | zoom-in | whoosh, hit | - |

## Notas
- Cambio de visual aproximadamente cada 1.5 a 3 s, siguiendo el ritmo de la locución (no es una regla fija).
- Respeta las zonas seguras y las reglas de `claude.md`.
- Los ejemplos de arriba son de muestra; bórralos al crear un beat map real.
