# Perfiles

Un perfil guarda la identidad de un cliente, marca o sector: voz, estilo visual, música y datos del negocio. El motor (código, skills, reglas de `claude.md`) es el mismo para todos; lo que cambia es el perfil.

## Estructura
```text
profiles/
├── ACTIVE                 # nombre del perfil en uso (una línea)
├── _template/             # copia esta carpeta para crear un perfil nuevo
└── <nombre>/
    ├── profile.json       # tema, fuentes, música, formato (lo leen los scripts y Remotion)
    ├── voice.md           # tono y palabras prohibidas
    ├── brand.md           # paleta, logos, referencias visuales
    ├── business_overview.md
    ├── pov.md
    └── stories.md
```

## Crear un perfil
```bash
cp -R profiles/_template profiles/mi-cliente && echo "mi-cliente" > profiles/ACTIVE
```
Luego llena los archivos. Se puede sobreescribir el perfil activo con `--profile <nombre>` en los scripts o indicándoselo a Claude.

## Precedencia
1. Regla absoluta de `claude.md` (no inventar datos): nunca se anula.
2. El perfil activo (colores, fuentes, música, voz, frases prohibidas adicionales).
3. Valores por defecto de `claude.md`.

## Quién lee qué
- Gonzalo (Remotion): `profile.json` > `theme` y `format`.
- Carlos (audio): `profile.json` > `audio`.
- Juan / Claude: todos los `.md` del perfil.

## Privacidad
Un perfil puede incluir historias y datos de negocio de un cliente. Mantén el repo privado y no subas información de clientes que no hayan autorizado.
