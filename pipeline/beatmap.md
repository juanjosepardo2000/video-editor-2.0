# BeatMap

> **ESTADO: FIXTURE DE PRUEBA, APROBADO por Juan (2026-10-17).** Guion ficticio para validar el pipeline (Remotion, exportador y mezcla). No es contenido de un video real; se reemplaza cuando Carlos entregue un transcript real.
> Contrato entre Juan (lo escribe), Gonzalo (lee `Escena`, `Visual`, `Transición`, `Caption`) y Carlos (lee `SFX`).
> No cambies los nombres de columna ni los códigos de escena sin avisar a los tres.

## Configuración global
- Perfil: `viral-dinamico` (debe coincidir con `profiles/ACTIVE`)
- Tema, acento, fuentes, formato y música: salen de `profiles/<perfil>/profile.json` (no se repiten aquí)

## Códigos de escena
| Código | Significado |
|---|---|
| `CAPTIONS` | Hablante a pantalla completa + subtítulos |
| `CAPTION_UI` | Hablante + animación pequeña en el tercio inferior |
| `SPLIT` | Animación en la mitad superior, hablante en la inferior |
| `FULLSCREEN` | Animación al 100%, reemplaza al hablante |

## Beats
Tiempos en segundos sobre el video **ya cortado** (`mm:ss.s`). SFX: `tipo` o `tipo:archivo.wav`; `-` si no lleva. Transiciones válidas: `cut`, `fade`, `slide-up`, `zoom-in`.

| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 00:02.5 | Si editas videos cortos, esto te importa. | CAPTIONS | Hablante a pantalla completa, sin gráficos | cut | riser | importa |
| 2 | 00:02.5 | 00:05.0 | Tres errores arruinan tus ediciones. | CAPTION_UI | Tarjeta liquid glass con 3 círculos numerados en el tercio inferior | slide-up | pop | Tres |
| 3 | 00:05.0 | 00:08.0 | Primero: elementos gigantes. Hazlos un veinticinco por ciento más pequeños. | SPLIT | Arriba: icono que se reduce un 25%; abajo: hablante | fade | whoosh | 25% |
| 4 | 00:08.0 | 00:10.5 | Segundo: colores puros. Los apagados se ven más premium. | SPLIT | Arriba: tres cajas de color, de saturado a apagado; abajo: hablante | fade | pop | apagados |
| 5 | 00:10.5 | 00:13.0 | Tercero: texto fuera de la zona segura. | FULLSCREEN | Diagrama 9:16 con zonas de la interfaz marcadas y un texto fuera de zona | zoom-in | whoosh, hit | zona segura |
| 6 | 00:13.0 | 00:15.0 | Corrige esto y tus videos subirán de nivel. | CAPTIONS | Hablante a pantalla completa, sin gráficos | cut | - | nivel |

## Notas
- Cambio de visual aproximadamente cada 1.5 a 3 s (guía, no regla fija).
- Respeta las zonas seguras y las reglas de `claude.md`.
- Transcript de prueba con tiempos por palabra: `pipeline/examples/transcript.fixture.json`.
