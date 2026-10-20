# Perfiles de edición

Un perfil es un **estilo de edición** reutilizable: cómo se corta, qué ritmo tiene, qué tipos de escena predominan, cuánto SFX lleva, cómo se ven los subtítulos y qué paleta, fuentes y música usa. El motor (código, skills, `claude.md`) es el mismo; la empresa elige el perfil que quiere aplicar. Cada empresa puede duplicar un perfil y ajustarlo a su marca.

## Estado de un perfil
`profile.json` > `status`: `en construccion` (reglas provisionales) o `calibrado` (reglas medidas a partir de videos de referencia). Antes de editar, Claude pregunta qué perfil usar y muestra este estado. Guía para calibrar: `docs/guia-estilos-y-criterio.md`.

## Perfiles incluidos
| Perfil | Para qué sirve |
|---|---|
| `viral-dinamico` | Reels/TikTok/Shorts de ritmo rápido y mucho SFX |
| `corporativo-sobrio` | Institucional: ritmo calmado, poco SFX, colores apagados |
| `perfil-1` | En construcción: se calibrará con los videos de referencia del equipo |
| `_template` | Plantilla para crear uno nuevo |

Los valores de `editing` de los dos perfiles de ejemplo son **propuestas iniciales** que hay que calibrar con videos reales; las fuentes solo respaldan el estilo viral (cambio visual cada ~1.5 a 3 s).

## Estructura de un perfil
```text
profiles/<nombre>/
├── profile.json           # parámetros de edición, tema, música, formato (lo leen los scripts y Remotion)
├── voice.md               # tono y palabras prohibidas
├── brand.md               # paleta, logos, referencias visuales
├── business_overview.md   # contexto de la empresa
├── pov.md
└── stories.md
```

`profiles/ACTIVE` contiene el nombre del perfil en uso.

## `profile.json`
- `editing.cutPaddingMs`: padding de corte (rango permitido 20 a 150).
- `editing.silenceThresholdSec`: silencio mínimo que se elimina.
- `editing.sceneChangeSec`: cadencia orientativa de cambio visual (guía, no regla fija).
- `editing.sceneMix`: proporción aproximada de tipos de escena (guía para el beat map).
- `editing.sfxDensity`: `baja`, `media` o `alta`.
- `editing.captionStyle`: `word-by-word` o `phrase`.
- `theme`, `audio`, `format`: lo que usan Remotion y la mezcla de audio.

## Crear un perfil
```bash
cp -R profiles/_template profiles/mi-perfil && echo "mi-perfil" > profiles/ACTIVE
```

## Precedencia
1. Regla absoluta de `claude.md` (no inventar datos) y zonas seguras: nunca se anulan.
2. Perfil activo.
3. Valores por defecto de `claude.md`.

## Quién lee qué
- Carlos: `editing.cutPaddingMs`, `editing.silenceThresholdSec` y `audio`.
- Gonzalo: `theme`, `format` y `editing.captionStyle`.
- Juan / Claude: `editing.*` y los `.md` al armar el beat map.
