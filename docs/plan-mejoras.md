# Plan de mejoras: de prototipo a edición con criterio

Estado de partida: el flujo completo corre (transcribir, cortar, beat map, mezcla, overlay, proyecto CapCut). Falta que la edición **decida bien** y se vea profesional. Este plan está pendiente de aprobación de Juan.

## 1. Idea central: un "director editorial" que decide, y un motor que obedece

```text
Video crudo
  -> [Carlos] transcribir + cortar + rostro (face_boxes.json) + métricas
  -> [Claude, director] beat map con criterio: qué mostrar, dónde, con qué B-roll y SFX
  -> [Gonzalo] compositor adaptativo: coloca capas sin tapar el rostro ni la zona segura
  -> [Carlos] audio profesional (ducking, loudness, stems)
  -> [QC automático] informe + MP4 de revisión
  -> [Gonzalo] proyecto CapCut con capas nativas
```

Reparto de responsabilidades: **Claude decide qué y por qué** (criterio editorial); **el código decide dónde** (geometría, sin inventar); **los perfiles** guardan el estilo.

## 2. Mejoras y quién las hace

### A. Colocación de tarjetas sin tapar la cara (la mejora más urgente)
- **Carlos** `src/backend/face_tracker.py`: detecta el rostro (MediaPipe u OpenCV, en CPU) y escribe `pipeline/face_boxes.json`.
- **Gonzalo** compositor: para cada escena calcula las zonas libres (fuera del rostro y de las zonas seguras) y mueve o reduce la tarjeta; suaviza el movimiento. En `SPLIT` el gráfico va arriba y el hablante abajo; en `FULLSCREEN` el hablante se oculta de verdad.
- **Claude** solo propone una preferencia (`arriba`, `abajo`, `lado`) en el beat map; la decisión final es del compositor.

### B. Criterio editorial (el "ojo profesional")
- **Claude** crea la skill `director-editorial` con una rúbrica que enlaza mensaje y recurso:

| Lo que se dice | Recurso |
|---|---|
| Una cifra o estadística | Contador animado |
| Una comparación (vs, antes/después) | Pantalla dividida |
| Un titular, noticia o cita | Resaltado de noticia |
| Una pregunta o búsqueda | Barra de búsqueda animada |
| Lista o pasos | Tarjeta numerada |
| Un concepto abstracto o escenario | B-roll |
| Explicación normal | Solo subtítulos |

- Reglas de densidad en cada perfil (propuestas a calibrar con los videos de referencia): máximo de capas llamativas simultáneas, separación mínima entre gráficos, porcentaje del video con gráficos, variedad de animaciones.
- **Claude** también corrige la transcripción (errores como "conía") y marca tomas falsas semánticas en `pipeline/cuts.json`, que **Carlos** ejecuta.

### C. Aprender estilos de videos de referencia (10 a 30)
- **Juan** elige y clasifica los videos por estilo (por ejemplo viral, corporativo, educativo).
- **Carlos** `src/backend/style_analyzer.py` mide: duración de planos (detección de cortes), pausas, palabras por minuto, nivel de música y voz, densidad de efectos.
- **Claude** revisa fotogramas muestreados (frecuencia de gráficos, tamaño de subtítulos, transiciones) y escribe las reglas medibles en `profiles/<estilo>/profile.json` y `style_guide.md`.
- Los videos **no se copian ni se suben al repo**: solo se guardan métricas derivadas.

### D. B-roll: material propio, Pexels e IA
Orden de preferencia: **1) material propio, 2) Pexels (gratis), 3) Higgsfield (de pago, con aprobación)**.
- **Claude** decide qué escenas necesitan B-roll, escribe las palabras de búsqueda y elige entre candidatos; usa `higgsfield-budget` si ninguno sirve.
- **Carlos** `src/backend/broll_search.py`: consulta la API de Pexels (vertical, duración adecuada), descarga a `pipeline/broll/` (ignorado por Git) y guarda `pipeline/broll_credits.json`.
- **Gonzalo**: escenas con video de fondo (recorte vertical, movimiento suave, oscurecido para legibilidad).
- **Juan**: consigue la clave gratuita de Pexels y la guarda en `.env` (nunca en el repo).

### E. Audio profesional (Carlos)
Reducción automática de la música cuando hay voz (ducking), normalización de la voz, control de picos, SFX según el tipo de animación, fundidos reales, cortes naturales (conservar respiraciones, microfundidos) y **pistas separadas** (voz, música, SFX) para CapCut. Ya corregidos: fundido de SFX, SFX repetidos, `.DS_Store`, nivel relativo a la voz.

### F. Control de calidad automático (Gonzalo + Carlos, orquesta Claude)
Informe `pipeline/qc_report.json` y MP4 ligero `out/qc/review.mp4`:
- **Geometría** (Gonzalo): rostro libre y zona segura, comprobados con las cajas reales del overlay y `face_boxes.json`; contraste de texto; ausencia de capas superpuestas.
- **Medios** (Carlos): pantallas negras, loudness y picos, duración, resolución, sincronía de subtítulos.
- **Visión** (Claude, sub-agentes): ortografía, legibilidad, errores de la lista de 6.

### G. CapCut con capas nativas
- **Juan** crea en CapCut una **plantilla maestra** con todas las pistas: video, overlay, audio (3 pistas), texto y un zoom con fotogramas clave.
- **Gonzalo** amplía `build_capcut_from_template.py` para rellenar subtítulos, zooms y audio como capas editables. Es la vía oficial porque ya abre en CapCut 9.4.0; el exportador de esquema propio queda como respaldo.
- Medios siempre en `~/Movies/editor-ia/` (CapCut no puede leer Escritorio ni Descargas).

### H. Entrada real y sincronizada (Carlos + Claude)
Rough cut definitivo; transcript regenerado tras el corte; beat map que cubra **todo** el video; un solo comando que ejecute el flujo con puntos de aprobación (skill `editar-video`).

## 3. Contratos nuevos (hay que acordarlos antes de programar)
1. `pipeline/face_boxes.json`: `{fps, width, height, frames:[{t, boxes:[{x,y,w,h,conf}]}]}`, coordenadas 0 a 1, muestreo a 10 fps y suavizado.
2. Beat map: columna nueva **`B-roll`** después de `Texto en pantalla`, con `-`, `own:archivo`, `stock:palabras clave` o `ai:prompt`, más una columna `Zona` opcional (`arriba`, `abajo`, `lado`, `auto`). Cambia el contrato de columnas: avisar a los tres.
3. `pipeline/cuts.json`: `[{start, end, reason}]` en tiempos del video original.
4. `profile.json`: campos nuevos en `editing` (`maxSimultaneousLayers`, `minGapBetweenGraphicsSec`, `graphicsCoverageTarget`, `captionFontScale`).
5. `pipeline/qc_report.json` y `out/qc/review.mp4`.

## 4. Hitos y criterios de aceptación

| Hito | Contenido | Se acepta cuando |
|---|---|---|
| **H1. Composición segura** | A, parte de H | En un video de 60 s, ninguna capa toca el rostro (comprobado por QC) |
| **H2. Criterio editorial** | B, F (geometría) | El beat map elige recursos por mensaje y respeta las reglas de densidad |
| **H3. Audio profesional** | E, F (medios) | Música baja sola con voz, sin picos, 3 pistas separadas |
| **H4. B-roll** | D | Un video con B-roll de Pexels y sin copyright, créditos guardados |
| **H5. Estilos aprendidos** | C | 2 o 3 perfiles calibrados con referencias, que cambian el resultado visiblemente |
| **H6. CapCut profesional** | G | Capas editables en CapCut, abre sin avisos |
| **H7. Prueba final** | Todo | Video de 60 a 90 s con 2 perfiles, informe de QC en verde |

H1 y H4 pueden avanzar en paralelo. H5 depende de la lista de referencias de Juan y empieza ya.

## 5. Riesgos
- **Detección de rostro:** de perfil, con manos o mala luz puede fallar; el QC debe marcarlo, no esconderlo.
- **Pexels:** licencia gratuita (revisar sus términos vigentes), límites de la API y poco B-roll vertical; Higgsfield es el respaldo.
- **Videos de referencia:** solo para métricas; no redistribuirlos.
- **Formato privado de CapCut:** cambia entre versiones; mantener la plantilla maestra actualizada.
- **Mac sin GPU y poco disco:** la detección de rostro y el análisis deben ir muestreados; limpiar `pipeline/` y `out/` entre pruebas.
- **Costos de visión:** revisar fotogramas muestreados, no todos.

## 6. Qué necesito de Juan
1. Aprobar este plan (o recortarlo).
2. 10 a 30 videos de referencia clasificados por estilo (enlaces o archivos).
3. Clave de Pexels en `.env`.
4. Plantilla maestra de CapCut.
5. 2 o 3 videos de prueba más: uno con cifras y comparaciones, uno de 60 s o más, y uno con otra persona o encuadre.
6. Decidir si se unen las ramas actuales a `main` antes de empezar H1.
