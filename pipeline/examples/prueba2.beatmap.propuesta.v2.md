# BeatMap

> **PROPUESTA del director editorial con `perfil-1`** para `assets/raw/prueba2.mp4` (pendiente de aprobación de Juan).
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
Tiempos en segundos sobre el video **ya cortado** (`mm:ss.s`; dos decimales si el hueco entre palabras es menor de 0.1 s). SFX: `tipo` o `tipo:archivo.wav`; `-` si no lleva. Prefijos válidos de `B-roll`: `own:`, `stock:`, `ai:`. Transiciones válidas: `cut`, `fade`, `slide-up`, `zoom-in`.

| # | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | B-roll | Zona | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 00:01.5 | GTA 6 acaba de revelar | FULLSCREEN | [interludio] Texto cinético «GTA 6» a pantalla completa en el primer segundo (hook); reemplaza al hablante | GTA 6 | - | auto | cut | hit | GTA 6 |
| 2 | 00:01.5 | 00:04.87 | algo que podría cambiarlo todo y no estoy hablando de sus gráficos. | CAPTIONS | [hablante] Hablante con subtítulo grande en la palabra clave; sin gráficos | - | - | auto | zoom-in | - | cambiarlo |
| 3 | 00:04.87 | 00:06.9 | Rockstar acaba de lanzar un nuevo trailer y | CAPTION_UI | [tarjeta] Tarjeta pequeña con el tema; no tapa el rostro | Nuevo trailer | - | auto | slide-up | pop | trailer |
| 4 | 00:06.9 | 00:10.95 | hay algo mucho más interesante detrás de toda esa locura de Bay City. | CAPTIONS | [hablante] Plano abierto sin gráficos; descanso visual | - | - | auto | cut | - | Bay City. |
| 5 | 00:10.95 | 00:13.0 | Esta vez seguimos a Jason y Lucía, | CAPTION_UI | [tarjeta] Tarjeta pequeña con los nombres de los protagonistas; no tapa el rostro | Jason y Lucía | - | auto | slide-up | pop | Jason |
| 6 | 00:13.0 | 00:17.09 | una pareja que demuestra de un golpe que sale terriblemente mal | CAPTIONS | [hablante] Punch-in 110% sobre el hablante para variar el encuadre | - | - | auto | zoom-in | - | terriblemente |
| 7 | 00:17.09 | 00:20.0 | y terminan atrapados en una conspiración criminal | FULLSCREEN | [broll] Video de apoyo oscurecido a pantalla completa: investigación criminal; reemplaza al hablante | Conspiración criminal | stock:criminal investigation board | auto | fade | whoosh | conspiración criminal |
| 8 | 00:20.0 | 00:22.7 | que se extiende por todo el estado de la unidad. | CAPTIONS | [hablante] Plano abierto sin gráficos; descanso tras el B-roll | - | - | auto | cut | - | estado |
| 9 | 00:22.7 | 00:25.64 | Y lo impresionante es que no estamos hablando solamente de una ciudad. | CAPTIONS | [hablante] Punch-in 110% sobre el hablante | - | - | auto | zoom-in | - | ciudad. |
| 10 | 00:25.64 | 00:28.98 | Rockstar promete una evolución gigantesca de su mundo abierto | FULLSCREEN | [broll] Video de apoyo a pantalla completa: ciudad costera vista desde el aire; reemplaza al hablante | Mundo abierto | stock:miami beach skyline aerial | auto | fade | whoosh | evolución gigantesca |
| 11 | 00:28.98 | 00:31.0 | con un Vice City completamente renovado. | CAPTIONS | [hablante] Plano abierto sin gráficos; descanso tras el B-roll | - | - | auto | cut | - | renovado. |
| 12 | 00:31.0 | 00:34.08 | Y lo mejor, GTA 6 llega este 19 de noviembre | FULLSCREEN | [cifra] Fecha grande a pantalla completa (dato clave); reemplaza al hablante | 19 de noviembre | - | auto | zoom-in | pop | 19 de noviembre |
| 13 | 00:34.08 | 00:37.4 | a Playstation 5 y Xbox Series X y S | CAPTIONS | [hablante] Plano abierto sin gráficos; las plataformas se leen en subtítulos | - | - | auto | cut | - | Playstation 5 |
| 14 | 00:37.4 | 00:40.7 | después de 13 años desde que salió GTA 5. | FULLSCREEN | [contador] Contador animado de 0 a 13 con la etiqueta «años» a pantalla completa | 13 años | - | auto | slide-up | pop | 13 años |
| 15 | 00:40.7 | 00:42.4 | Pero aquí viene la verdadera pregunta, | CAPTIONS | [hablante] Punch-in 110% antes de la pregunta | - | - | auto | zoom-in | - | pregunta, |
| 16 | 00:42.4 | 00:46.6 | GTA 6 va a superar todas las expectativas y el hype que se ha planteado | CAPTION_UI | [titular] Titular pequeño con la pregunta central; no tapa el rostro | Superar todas las expectativas | - | auto | slide-up | pop | expectativas |
| 17 | 00:46.6 | 00:50.0 | o crees que esto se queda demasiado grande? Te leo en los comentarios. | CAPTIONS | [hablante] Cierre limpio con la invitación a comentar, sin gráficos | - | - | auto | cut | hit | comentarios. |
