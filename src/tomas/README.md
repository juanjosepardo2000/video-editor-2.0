# Control de tomas (prototipo)

Tres servicios sobre un motor común (ficha por clip en caché), con panel local.

    ./scripts/panel_tomas.sh        # http://127.0.0.1:8765

1. **Clasificador** (`clasificador.py`): 7 criterios de la productora → semáforo, motivo, marcadores, carpetas buenas/malas/por revisar.
2. **Multicámara** (`multicam.py`): sincroniza clips de varias cámaras por el audio de la voz (GCC-PHAT).
3. **Maquetado** (`maquetado.py`): elige la mejor toma de cada línea del guion y corta muletillas, silencios, repeticiones y respiraciones.

Umbrales provisionales en `config/criterios.json`. Datos de trabajo en `tomas_data/` (fuera de Git).
Fidelidad al guion: juez local por defecto; con `ANTHROPIC_API_KEY` en el entorno se puede elegir el juez Claude para los casos dudosos.
Límites conocidos: clips sin audio no se sincronizan (se marcan para colocar a mano); la exportación a CapCut (`capcut.py`) está generada pero aún sin probar abriendo CapCut.
