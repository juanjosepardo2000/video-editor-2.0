# Reglas de estilo por defecto — ai-video-editor

## Tipografía
- Fuente principal: **Inter**. Alternativa para titulares: **CoolVetica**.
- Colocar los archivos en `assets/fonts/`.

## Formato y zonas seguras (9:16, 1080x1920)
- Mantener texto y gráficos fuera de las zonas de UI de la plataforma:
  - Superior: 150 px libres
  - Inferior: 380 px libres
  - Lateral derecho: 120 px libres
  - Márgenes laterales: 60 px

## Cortes de audio/video
- Padding de corte: mínimo **20 ms**, máximo **150 ms** alrededor de cada palabra conservada.

## Mezcla de audio
- Música de fondo entre **-20 dB y -23 dB** respecto a la voz.
- SFX a nivel perceptible sin tapar la voz.

## Convenciones
- Todo artefacto intermedio vive en `pipeline/`; renders finales en `out/`.
- Los videos fuente van en `assets/raw/` (no se versionan).
