# BeatMap

> **ESTADO: REAL, generado por Claude a partir del transcript de `assets/raw/prueba.mp4` (2026-10-17).** Aprobado por instrucción de Juan ("haz todo el flujo"); revisable.
> Contrato entre Juan (lo escribe), Gonzalo (lee `Escena`, `Visual`, `Texto en pantalla`, `Transición`, `Caption`) y Carlos (lee `SFX`).
> Contrato de columnas:
> - `Speech`: texto completo hablado; fuente de los subtítulos.
> - `Visual`: instrucción interna de diseño para elegir/componer el gráfico; **nunca se imprime**.
> - `Texto en pantalla`: único copy permitido dentro de tarjetas y gráficos (sale solo de lo dicho en `Speech` o del perfil activo; `-` si no corresponde).
> - `Caption`: 1 a 3 palabras literales de `Speech` que reciben el color de acento.
> No cambies los nombres de columna ni los códigos de escena sin avisar a los tres.

## Configuración global
- Perfil: `viral-dinamico` (debe coincidir con `profiles/ACTIVE`)
- Tema, acento, fuentes, formato y música: salen de `profiles/<perfil>/profile.json` (no se repiten aquí)

## Códigos de escena
| Código | Significado |
|---|---|---|---|---|---|---|---|---|---|
| `CAPTIONS` | Hablante a pantalla completa + subtítulos |
| `CAPTION_UI` | Hablante + animación pequeña en el tercio inferior |
| `SPLIT` | Animación en la mitad superior, hablante en la inferior |
| `FULLSCREEN` | Animación al 100%, reemplaza al hablante |

## Beats
Tiempos en segundos sobre el video **ya cortado** (`mm:ss.s`). SFX: `tipo` o `tipo:archivo.wav`; `-` si no lleva. Transiciones válidas: `cut`, `fade`, `slide-up`, `zoom-in`.

| # | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 00:03.2 | hola este es un test para probar | CAPTIONS | Hablante a pantalla completa, sin gráficos | - | cut | - | test |
| 2 | 00:03.2 | 00:08.3 | si el editor de vídeos funciona correctamente este ok ya me acordé | CAPTION_UI | Tarjeta liquid glass en el tercio inferior con el tema | Editor de vídeos | slide-up | pop | funciona correctamente |
| 3 | 00:08.3 | 00:11.7 | si el punto es probar que el asistente de vídeos | FULLSCREEN | Diagrama simple a pantalla completa del asistente de vídeos | Asistente de vídeos | zoom-in | whoosh | asistente |
| 4 | 00:11.7 | 00:14.9 | conía funcione tanto con los cambios que hizo Carlos y | SPLIT | Arriba: tarjeta con los cambios del equipo; abajo: hablante | Cambios de Carlos | fade | pop | Carlos |
| 5 | 00:14.9 | 00:16.1 | mi persona y Gonzalo. | CAPTIONS | Hablante a pantalla completa, cierre | - | cut | hit | Gonzalo. |

## Notas
- Cambio de visual aproximadamente cada 1.5 a 3 s (guía, no regla fija).
- Respeta las zonas seguras y las reglas de `claude.md`.
- La columna `Caption` debe coincidir literalmente con palabras de `Speech` (el resaltado busca coincidencias con el texto hablado).
- Sin `riser` en esta prueba: dura ~9 s y taparía la voz del video de 16 s.
- Fixture anterior (guion ficticio): `pipeline/examples/beatmap.fixture.md`.
