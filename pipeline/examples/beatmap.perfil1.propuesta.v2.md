# BeatMap

> **PROPUESTA del director editorial con `perfil-1`** para `assets/raw/prueba.mp4` (pendiente de aprobación de Juan).
> Contrato entre Juan (lo escribe), Gonzalo (lee `Escena`, `Visual`, `Texto en pantalla`, `Transición`, `Caption`) y Carlos (lee `SFX`).
> Contrato: v2 (acepta también v1 durante la transición; sin `B-roll` se asume `-` y sin `Zona`, `auto`).
> Contrato de columnas:
> - `Speech`: texto completo hablado; fuente de los subtítulos.
> - `Visual`: instrucción interna de diseño para elegir/componer el gráfico; **nunca se imprime**.
> - `Texto en pantalla`: único copy permitido dentro de tarjetas y gráficos (sale solo de lo dicho en `Speech` o del perfil activo; `-` si no corresponde).
> - `B-roll`: `-`, `own:archivo` (de `assets/`), `stock:palabras` (Pexels) o `ai:prompt` (Higgsfield, con presupuesto aprobado).
> - `Zona`: `arriba`, `abajo`, `lado` o `auto`; es una **preferencia**, el compositor decide la posición final para no tapar el rostro.
> - `Caption`: 1 a 3 palabras literales de `Speech` que reciben el color de acento.
> No cambies los nombres de columna ni los códigos de escena sin avisar a los tres.

## Configuración global
- Perfil: `perfil-1` (debe coincidir con `profiles/ACTIVE`)
- Tema, acento, fuentes, formato y música: salen de `profiles/<perfil>/profile.json` (no se repiten aquí)

## Códigos de escena
| Código | Significado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `CAPTIONS` | Hablante a pantalla completa + subtítulos |
| `CAPTION_UI` | Hablante + animación pequeña en el tercio inferior |
| `SPLIT` | Animación en la mitad superior, hablante en la inferior |
| `FULLSCREEN` | Animación al 100%, reemplaza al hablante |

## Beats
Tiempos en segundos sobre el video **ya cortado** (`mm:ss.s`). SFX: `tipo` o `tipo:archivo.wav`; `-` si no lleva. Prefijos válidos de `B-roll`: `own:`, `stock:`, `ai:`. Transiciones válidas: `cut`, `fade`, `slide-up`, `zoom-in`.

| # | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | B-roll | Zona | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 00:03.2 | hola este es un test para probar | CAPTIONS | [hablante] Hook: palabra clave 'test' en grande desde el primer segundo, sin gráficos | - | - | auto | cut | - | test |
| 2 | 00:03.2 | 00:04.6 | si el editor de vídeos | CAPTION_UI | [tarjeta] Tarjeta pequeña con el tema; no tapa el rostro | Editor de vídeos | - | auto | slide-up | pop | editor |
| 3 | 00:04.6 | 00:08.3 | funciona correctamente este ok ya me acordé | CAPTIONS | [hablante] Punch-in 110% sobre el hablante para variar el encuadre | - | - | auto | zoom-in | whoosh | correctamente |
| 4 | 00:08.3 | 00:11.6 | si el punto es probar que el asistente de vídeos | FULLSCREEN | [broll] Video de apoyo a pantalla completa, oscurecido para legibilidad; reemplaza al hablante | Asistente de vídeos | stock:video editing software screen | auto | fade | whoosh | asistente |
| 5 | 00:11.6 | 00:14.9 | conía funcione tanto con los cambios que hizo Carlos y | CAPTIONS | [hablante] Primer plano sin gráficos; descanso visual tras el B-roll | - | - | auto | cut | - | Carlos |
| 6 | 00:14.9 | 00:16.1 | mi persona y Gonzalo. | CAPTIONS | [hablante] Cierre limpio sin gráficos | - | - | auto | cut | hit | Gonzalo. |
