# Riesgos del exportador CapCut

El exportador actual genera un borrador experimental sin abrir CapCut. Antes de
adaptarlo a una instalación real hacen falta la versión exacta de CapCut, la
versión de macOS y un proyecto vacío creado por esa misma instalación.

- `draft_content.json` no es un contrato público y puede cambiar entre versiones.
- CapCut puede registrar medios y líneas de tiempo en archivos adicionales o
  campos internos que un JSON generado externamente no reproduce.
- Algunas versiones pueden proteger, migrar o rechazar borradores externos.
- Abrir un borrador incompatible podría hacer que CapCut lo repare, lo ignore o
  lo marque como corrupto; la prueba debe realizarse sobre una copia.
- Las rutas de medios son distintas entre Windows y macOS y deben reconstruirse
  en el equipo destino.

Orden acordado de mitigación:

1. Probar una copia del proyecto generado en la versión objetivo.
2. Si falla, rellenar una copia de un proyecto vacío creado por esa instalación.
3. Si también falla, implementar FCPXML para DaVinci Resolve / Final Cut. EDL no
   conserva adecuadamente overlays, estilos de subtítulos ni keyframes.

No se implementará una adaptación específica ni FCPXML hasta observar el fallo
real y conservar una muestra del proyecto vacío, evitando inventar su esquema.

