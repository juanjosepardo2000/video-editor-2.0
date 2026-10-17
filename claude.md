# REGLAS DEL EDITOR DE VIDEO — ai-video-editor

Lee este archivo completo antes de cualquier tarea de edición. Si el usuario te corrige, actualiza este archivo (ver "Aprendizaje continuo").

## 0. Regla absoluta
- Nunca inventes datos, cifras, fechas ni afirmaciones que no estén en `pipeline/transcript.json` o en `context/`.
- Si falta un dato, pregunta; no lo rellenes.

## 1. Flujo y contratos de archivos
| Archivo / carpeta | Dueño | Contenido |
|---|---|---|
| `assets/raw/` | Carlos | Video crudo (no se versiona) |
| `assets/sfx/`, `assets/music/`, `assets/fonts/` | Carlos | Recursos de audio y fuentes |
| `pipeline/transcript.json` | Carlos | Timestamps por palabra |
| `pipeline/beatmap.md` | Juan | Plan escena por escena |
| `src/graphics/` | Gonzalo | Componentes Remotion |
| `src/nle_bridge/` | Gonzalo | Exportador CapCut / DaVinci |
| `out/` | todos | Renders finales (no se versiona) |
| `context/` | Juan | Voz, marca, historias |

Orden: rough cut -> beat map (aprobación humana) -> gráficos -> sonido -> QC loop -> export.
No avances al siguiente paso sin aprobación del usuario sobre el beat map.

## 2. Corte de voz
- Transcripción a nivel de palabra (WhisperX o 11Labs Scribe).
- Elimina silencios > 0.5 s, muletillas y tomas falsas; conserva solo la última toma limpia de cada frase.
- Padding de corte: **20 ms a 150 ms** (por defecto ~20 ms en cortes de voz); nunca cortes una respiración de forma abrupta ni una palabra a la mitad.
- Antes de procesar el video completo, prueba con los primeros 10 segundos.

## 3. Tipografía
- Principal: **Inter Semibold**. Titulares/llamadas de alto impacto: **CoolVetica**.
- Subtítulos virales: una sans media para palabras normales + una script para palabras de acento.
- Contadores/datos numéricos: fuente tipo reloj digital (solo si el beat map lo pide).
- **Reduce todo tamaño un 25% respecto al valor por defecto.** Iconos y formas gigantes delatan a un editor principiante.
- Si el texto se ve apretado, baja el tamaño de fuente.

## 4. Color y estética
- Colores sobrios y apagados (azules y verdes opacos). Los colores apagados se ven más premium.
- Evita negros puros, blancos puros y rojos saturados, y amarillos fosforescentes, salvo que se pidan.
- Tema por defecto: claro estilo Apple con un solo acento (naranja), o paleta oscura sobria si `context/brand.md` lo indica.
- Tarjetas de UI: estilo Apple / liquid glass.
- LUTs `.cube`: sombras levantadas, luces suaves, tonos peach en altas luces, saturación y contraste bajos, sin teal en sombras; aplicar al ~50%.

## 5. Zonas seguras 9:16 (1080x1920)
- Texto y gráficos lejos de los bordes superior e inferior y de los laterales extremos (UI de TikTok/Reels/Shorts).
- Valores de trabajo provisionales (las fuentes NO dan cifras exactas, ajustar tras pruebas): superior 150 px, inferior 380 px, derecha 120 px, márgenes laterales 60 px.
- Animaciones y subtítulos en la mitad inferior de la pantalla, sin tapar nunca el rostro del hablante.

## 6. Subtítulos y animaciones
- Subtítulos palabra por palabra (pop-up con fade), resaltando 1 a 3 palabras clave con el color de acento.
- Tipos de escena: **Captions puro**, **Caption + UI flotante**, **Split Screen 50/50**, **Fullscreen Motion Graphic**.
- Regla de los 3 objetos: objeto principal al centro, elementos de apoyo en los bordes, elementos de profundidad alrededor.
- Fondo detrás de una animación en pantalla: oscurecido y desenfocado.
- Aparición de tarjetas de texto: ~2 s. Sin parpadeos de 1 fotograma. Texto con velocidad suficiente para leerse.
- Render: desactiva motion blur salvo que se pida; revisiones en media resolución; render final a 4K (fondo transparente en overlays).

## 7. Audio
- Música de fondo entre **-20 dB y -23 dB** durante la voz (referencia: -22 dB).
- SFX por evento visual: whoosh en zooms/transiciones, pop/click en elementos de UI, riser en clímax.
- Usa solo archivos de `assets/sfx/` y `assets/music/`.

## 8. Redacción (anti-slop)
- Prohibido: "in today's fast-paced world", "in today's digital age", "landscape", "in an era where", "in a world where" y equivalentes en español ("en el mundo acelerado de hoy", "en la era digital").
- Tono y reglas detalladas en `context/voice.md`.

## 9. QC loop (antes de entregar)
Usa la skill `qc-loop`: muestrea el render a **10 fps** (1 fps pasa por alto la mayoría de errores) y revisa en paralelo con los sub-agentes de `.claude/agents/`. Busca:
1. Animaciones repetidas.
2. Destellos de 1 fotograma.
3. Texto ilegible por velocidad.
4. Elementos tapando la cara del hablante.
5. Palabras repetidas no cortadas.
6. Desincronización de labios.
7. Texto fuera de zona segura.
Si hay fallos, corrige y vuelve a renderizar. Si tras 3 iteraciones persisten, pide ayuda al usuario.

## 9b. Generación con Higgsfield
Antes de cualquier generación, sigue la skill `higgsfield-budget` (confirmar aspecto, modelo, costo y prompt).

## 10. Aprendizaje continuo
Cuando el usuario corrija algo o edite el resultado final:
1. Identifica la regla que falló o faltó.
2. **Modifica o reescribe** esa regla aquí (no añadas duplicados; evita el "context bloat").
3. Anótalo en el registro de abajo.

### Registro de cambios
- (vacío)
