# Roadmap de Gonzalo - Motion Graphics e integración NLE

Esta es la guía de trabajo de Gonzalo dentro de `ai-video-editor`. Debe mantenerse actualizada a medida que se completen pruebas o cambie un contrato compartido.

## 1. Misión y límites

Gonzalo es responsable de convertir el BeatMap aprobado en gráficos animados reutilizables y en una línea de tiempo que pueda continuar en CapCut.

### Carpetas permitidas

- `src/graphics/`: componentes, composiciones, parser visual y fixtures propios.
- `src/nle_bridge/`: exportadores de líneas de tiempo.
- `package.json`: comandos relacionados con gráficos y exportación.
- `out/`: renders y proyectos generados; no se versiona.

### Carpetas que no debe modificar

- `src/backend/`: pertenece a Carlos.
- `pipeline/`: pertenece a Juan y contiene los contratos compartidos.
- `assets/`: los medios finales los organiza Carlos.
- `context/` y `claude.md`: pertenecen a la dirección y orquestación de Juan.

Si Gonzalo necesita modificar el formato del BeatMap o del transcript, debe pedir el cambio a Juan o Carlos antes de programarlo.

## 2. Entradas y salidas de Gonzalo

### Entradas que debe recibir

| Entrada | Responsable | Uso |
|---|---|---|
| `claude.md` | Juan | Reglas visuales, zonas seguras, tipografía y calidad. |
| `pipeline/beatmap.md` | Juan | Escenas, visuales, transiciones, SFX y palabras de acento. |
| `pipeline/transcript.json` | Carlos | Tiempos exactos de cada palabra después del rough cut. |
| Rough cut final | Carlos | Vídeo ya limpio y cortado sobre el que se monta todo. |
| Audio final o voz | Carlos | Pista que se coloca en la línea de tiempo. |
| SFX y música | Carlos | Recursos señalados por Juan en el BeatMap. |

### Salidas que debe entregar

| Salida | Destino | Función |
|---|---|---|
| Componentes React tipados | `src/graphics/components/` | Biblioteca reutilizable de gráficos. |
| Composición basada en BeatMap | Remotion | Convierte el contrato de Juan en escenas. |
| Overlay transparente | `out/beatmap-overlay.mov` | Capa visual para colocar sobre el vídeo. |
| Proyecto CapCut | `out/capcut_project/` | Timeline con vídeo, overlays, audio, zooms y subtítulos. |
| Informe de validación | Proyecto CapCut generado | Evidencia de integridad antes de probar en CapCut. |

## 3. Contrato vigente

Gonzalo solo acepta el formato nuevo de `pipeline/beatmap.md`:

```text
# | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption
```

Reglas:

- Los tiempos usan `mm:ss.s` y pertenecen al vídeo ya cortado.
- `Escena` admite únicamente `CAPTIONS`, `CAPTION_UI`, `SPLIT` y `FULLSCREEN`.
- `Speech` contiene el texto completo que debe mostrarse como subtítulo.
- `Caption` solo identifica entre una y tres palabras que llevan color de acento.
- `Perfil` debe coincidir con `profiles/ACTIVE`; tema, colores, fuentes, formato y estilo de captions se leen desde `profiles/<perfil>/profile.json`.
- Si existe `pipeline/transcript.json`, sus timestamps tienen prioridad.
- Solo cuando el transcript no existe se reparten uniformemente las palabras dentro de cada escena.
- Un contrato inválido debe detener el proceso con un error claro; no se mantiene compatibilidad con formatos antiguos.

## 4. Estado general

| Fase | Estado | Resultado |
|---|---|---|
| Entorno Remotion | Completada | Studio en puerto 3000 y render transparente. |
| Biblioteca gráfica base | Completada | Cinco componentes reutilizables y tipados. |
| Integración BeatMap | Completada con fixtures | Parser estricto y composición automática. |
| Exportador CapCut | Prototipo validado localmente | Genera timeline y registra recursos sin abrir CapCut. |
| Prueba en CapCut macOS | Pendiente | Falta comprobar la versión real instalada. |
| Integración con medios reales | Bloqueada por entradas | Espera rough cut, transcript y BeatMap definitivos. |
| QC del vídeo real | Pendiente | Se ejecuta después de integrar los medios reales. |
| Entrega final | Pendiente | Requiere aprobación de Juan y prueba completa. |

## 5. Roadmap paso a paso

### Fase 0 - Sincronización antes de trabajar

- [x] Clonar el repositorio.
- [x] Actualizarlo con `git pull` y leer el contrato nuevo.
- [x] Leer `claude.md`, `README.md`, `pipeline/beatmap.md` y los stubs asignados.
- [ ] Antes de cada nueva sesión, revisar si Juan cambió el BeatMap o las reglas.
- [ ] Confirmar que no haya cambios locales ajenos antes de integrar trabajo nuevo.

Comandos:

```bash
git status --short
git pull --ff-only origin main
```

Criterio de salida: trabajar sobre la versión correcta sin sobrescribir archivos de Juan o Carlos.

### Fase 1 - Entorno Remotion

- [x] Configurar Remotion con React y TypeScript.
- [x] Hacer que `npm run studio` abra `localhost:3000`.
- [x] Configurar composiciones verticales a 1080x1920 y 30 fps.
- [x] Renderizar un MOV ProRes 4444 con transparencia.
- [x] Mantener secuencia PNG como respaldo de alfa.
- [x] Preparar una composición 4K vertical que conserve las proporciones del diseño 1080p.
- [ ] Ejecutar el render final 4K completo cuando el vídeo real esté aprobado.

Comandos:

```bash
npm install
npm run studio
npm run render
npm run render:png
npm run still:4k
npm run render:4k
```

Criterio de salida: el overlay tiene canal alfa real, resolución correcta, 30 fps y no incluye un fondo sólido accidental.

Formato recomendado para CapCut: MOV ProRes 4444. Conserva bien los bordes semitransparentes del liquid glass y evita más artefactos que un códec de distribución. PNG RGBA es el respaldo si la versión instalada de CapCut interpreta mal el alfa del MOV.

### Fase 2 - Sistema visual y componentes reutilizables

- [x] Definir tokens de color, tipografía, espaciado y zonas seguras.
- [x] Crear `LiquidGlassCard`.
- [x] Crear `LiquidGlassCardV2` para overlay y fondos claros/oscuros.
- [x] Crear barra de búsqueda animada con error, borrado y corrección.
- [x] Crear resaltado editorial de noticias.
- [x] Crear contador numérico animado.
- [x] Crear subtítulos palabra por palabra con fade/pop y color de acento.
- [ ] Añadir nuevos componentes solo cuando un BeatMap real los necesite.
- [ ] Evitar componentes específicos de un único vídeo si pueden resolverse mediante props.

Reglas visuales obligatorias:

- Inter Semibold como fuente principal.
- Tamaños aproximadamente 25% menores que los valores genéricos.
- Un único acento naranja apagado por defecto.
- Evitar blanco, negro y rojo puros.
- Zona segura provisional: 150 px arriba, 380 px abajo, 120 px a la derecha y 60 px laterales.
- No tapar el rostro del hablante.
- No crear destellos o apariciones de un solo fotograma.
- Mantener cada tarjeta el tiempo suficiente para poder leerla.

Criterio de salida: cada componente acepta props tipadas, funciona con contenido variable y puede renderizarse tanto en demostración como en overlay.

### Fase 3 - Motor de BeatMap

- [x] Implementar el parser del contrato nuevo.
- [x] Validar encabezados, escenas, tiempos, solapamientos y campos obligatorios.
- [x] Detener el render con mensajes claros si el contrato no es válido.
- [x] Mapear los cuatro códigos de escena a composiciones visuales.
- [x] Usar `Speech` como texto completo de subtítulo.
- [x] Usar `Caption` únicamente para las palabras de acento.
- [x] Leer timestamps reales del transcript cuando existe.
- [x] Implementar reparto uniforme únicamente como fallback.
- [x] Probar el flujo con BeatMap y transcript ficticios.
- [x] Añadir pruebas automáticas del contrato válido, formato viejo, solapamientos y escenas desconocidas.
- [ ] Validar el contenido real cuando Juan publique el BeatMap definitivo.

Mapa de escenas:

| Código | Comportamiento visual |
|---|---|
| `CAPTIONS` | Hablante a pantalla completa con subtítulos. |
| `CAPTION_UI` | Hablante con animación pequeña en el tercio inferior. |
| `SPLIT` | Animación arriba y hablante abajo. |
| `FULLSCREEN` | El motion graphic sustituye temporalmente al hablante. |

Comandos:

```bash
npm run sync:beatmap
npm run sync:beatmap:fixture
npm run render:preview
npm run render
npm run render:fixture
```

Criterio de salida: el comienzo y final de cada escena coinciden con el BeatMap, y las palabras coinciden con los timestamps de Carlos cuando están disponibles.

### Fase 4 - Exportador CapCut

- [x] Investigar la estructura no oficial de los proyectos CapCut.
- [x] Separar `draft_info.json` para macOS y `draft_content.json` como espejo de compatibilidad.
- [x] Crear `draft_meta_info.json` para registrar los medios.
- [x] Copiar los recursos dentro del proyecto exportado.
- [x] Generar pista de rough cut cortada por beats.
- [x] Generar pista de overlays transparentes.
- [x] Generar pista de audio.
- [x] Generar subtítulos individuales por palabra.
- [x] Añadir zooms suaves mediante keyframes.
- [x] Validar referencias, intervalos, duración, medios y keyframes.
- [x] Probarlo con vídeo, audio y transcript ficticios.
- [x] Añadir pruebas automáticas de pistas, medios, mirrors, captions y keyframes.
- [ ] Ejecutar el exportador en el Mac de destino para regenerar rutas absolutas del sidecar.
- [ ] Colocar una copia en la carpeta de borradores de CapCut sin tocar proyectos existentes.
- [ ] Confirmar que la última versión instalada reconoce el proyecto y sus medios.
- [ ] Documentar cualquier ajuste específico de esa versión.

Comando de prueba actual:

```bash
npm run capcut:export:fixture
```

Comando general:

```bash
python3 src/nle_bridge/capcut_exporter.py \
  --rough-cut /ruta/al/rough-cut.mp4 \
  --overlay out/beatmap-overlay.mov \
  --audio /ruta/al/audio-final.wav \
  --beatmap pipeline/beatmap.md \
  --transcript pipeline/transcript.json \
  --output out/capcut_project \
  --project-name Minthy-Proyecto
```

Riesgos que deben seguir visibles:

- CapCut no publica un esquema estable para sus borradores.
- Los campos pueden cambiar entre versiones.
- La instalación de macOS puede usar rutas y estructuras distintas de Windows.
- El sidecar puede requerir rutas absolutas regeneradas en el Mac.
- Un JSON válido no garantiza que CapCut lo interprete igual.
- Nunca probar primero sobre una biblioteca o proyecto importante; utilizar una copia.

Criterio de salida: el proyecto aparece en CapCut, abre sin reparación, encuentra todos los medios, mantiene el alfa y reproduce zooms/subtítulos en sincronía.

### Fase 5 - Integración con archivos reales

Esta fase comienza cuando Carlos y Juan entreguen los contratos finales.

- [ ] Recibir el rough cut definitivo de Carlos.
- [ ] Recibir `pipeline/transcript.json` regenerado después de los cortes.
- [ ] Recibir y revisar el BeatMap aprobado de Juan.
- [ ] Comprobar que la duración del rough cut, transcript y BeatMap coincide.
- [ ] Sustituir fixtures por archivos reales sin cambiar el contrato.
- [ ] Renderizar primero únicamente los primeros 10 segundos.
- [x] Automatizar y validar el render de 10 segundos con recursos ficticios.
- [ ] Revisar sincronía, encuadre, alfa y legibilidad de esos 10 segundos.
- [ ] Obtener aprobación antes de renderizar el vídeo completo.
- [ ] Renderizar todos los overlays.
- [ ] Generar el proyecto CapCut real.

Criterio de salida: la prueba de 10 segundos funciona antes de gastar tiempo en el vídeo completo.

### Fase 6 - QC visual

Responsabilidad compartida: Gonzalo corrige los gráficos y Juan dirige/aprueba el QC.

Controles técnicos ya automatizados:

- [x] Pruebas del parser BeatMap.
- [x] Pruebas del exportador CapCut.
- [x] Comprobación TypeScript.
- [x] Comprobación de resolución, FPS, duración, codec y canal alfa.
- [x] Informe JSON del overlay 1080p, la muestra 4K y la prueba de 10 segundos.

- [ ] Muestrear el render a 10 fps.
- [ ] Buscar animaciones repetidas.
- [ ] Buscar destellos de un fotograma.
- [ ] Verificar que el texto permanezca el tiempo suficiente.
- [ ] Verificar que ningún elemento tape el rostro.
- [ ] Revisar palabras repetidas o incorrectas.
- [ ] Revisar sincronización entre voz, transcript y captions.
- [ ] Revisar las zonas seguras de TikTok, Reels y Shorts.
- [ ] Revisar overlay sobre fondo claro y fondo oscuro.
- [ ] Corregir y repetir el QC; máximo tres iteraciones antes de pedir ayuda.

Criterio de salida: cero fallos críticos y aprobación de Juan sobre el render revisado.

Comandos:

```bash
# Pruebas rápidas de código y contratos
npm test

# QC técnico sobre renders ya generados
npm run qc:technical

# Render y validación de los primeros 10 segundos
npm run qc:10s
```

### Fase 7 - Entrega e integración Git

- [ ] Ejecutar las comprobaciones técnicas finales.
- [ ] Confirmar que solo se modificaron carpetas permitidas.
- [ ] Informar a Juan de archivos, comandos y resultados.
- [ ] Subir los cambios a la rama o carpeta que Juan indique.
- [ ] Resolver conflictos sin sobrescribir trabajo de Carlos o Juan.
- [ ] Etiquetar claramente cualquier limitación pendiente de CapCut.

Comprobaciones:

```bash
npx tsc --noEmit
python3 -m py_compile src/nle_bridge/capcut_exporter.py
git diff --check
git diff --name-only -- src/backend pipeline
git status --short
```

Criterio de salida: las comprobaciones pasan, no hay cambios fuera del alcance y Juan puede integrar el trabajo sin reconstruirlo.

## 6. Dependencias entre integrantes

```text
Carlos: rough cut + transcript final
                  |
                  v
Juan: BeatMap aprobado + dirección visual
                  |
                  v
Gonzalo: gráficos + overlay + proyecto CapCut
                  |
                  v
Juan y Gonzalo: QC y aprobación
                  |
                  v
Entrega final
```

Gonzalo puede avanzar con fixtures cuando falten entradas, pero no debe afirmar que la integración real está terminada hasta recibir los archivos finales.

## 7. Definición de terminado

El trabajo completo de Gonzalo estará terminado cuando se cumplan todas estas condiciones:

- [ ] Los cinco componentes base funcionan y están documentados.
- [ ] El BeatMap real se interpreta sin advertencias inesperadas.
- [ ] Los captions usan el transcript posterior al corte.
- [ ] El overlay real se renderiza con alfa, 30 fps y resolución aprobada.
- [ ] Se verifican zonas seguras y rostro del hablante.
- [ ] El proyecto se genera sin abrir CapCut.
- [ ] El proyecto se reconoce en la versión macOS objetivo.
- [ ] CapCut encuentra vídeo, audio y overlays sin pedir relink.
- [ ] Los zooms y subtítulos están sincronizados.
- [ ] El QC visual no detecta fallos críticos.
- [ ] Juan aprueba el resultado.
- [ ] Los cambios se integran sin modificar `src/backend/` ni `pipeline/`.

## 8. Próximo paso inmediato

1. Copiar `out/capcut-project-fixture/` al Mac.
2. Regenerar allí el proyecto con `python3` para que el sidecar use rutas macOS.
3. Probarlo en una copia de la carpeta de borradores de la versión actual de CapCut.
4. Registrar qué archivos reconoce CapCut y cualquier mensaje de relink o reparación.
5. Ajustar el exportador solo con evidencia de esa prueba.
6. Después, esperar los medios reales de Carlos y el BeatMap definitivo de Juan.

## 9. Registro de avances

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-10-17 | Entorno Remotion, biblioteca gráfica, parser BeatMap y render transparente. | Completado con fixtures. |
| 2026-10-17 | Exportador experimental CapCut con medios, keyframes y captions. | Validado localmente; pendiente macOS. |

