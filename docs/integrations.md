# Integraciones MCP y APIs (referencia de Juan)

Fuente: tutoriales analizados en NotebookLM. Los pasos de conexión se hacen manualmente en la app de Claude (no se versionan).

## Higgsfield MCP
1. Copiar la URL del servidor desde Higgsfield, pestaña `MCP & CLI`.
2. Claude: `Settings > Connectors > Add Custom Connector` (o `Customize > Connectors`). Nombre: `Higgsfield`, pegar la URL, **Connect** y autorizar en el navegador.
3. `Configure (Higgsfield)`: poner **Needs Approval** solo en `generate_image` y `generate_video`; el resto en `Always Allow`.
4. Skill de control de gasto: `.claude/skills/higgsfield-budget/SKILL.md`.

## Descript MCP (alternativa de rough cut en la nube)
1. `Customize > Connectors` > `Descript` > Connect.
2. En permisos, poner la herramienta **Underlord** en `Always Allow` (si no, Claude pide confirmación en cada micro-corte).
3. Prompt de referencia:
```text
Open the Descript project at [URL]. Use Underlord to remove all filler words (ums, ahs) and shorten word gaps longer than 0.5 seconds down to 0.2 seconds. Remove any repeated sentences, keeping the last clean take.
```

## DaVinci Resolve MCP (long-form)
1. Clonar el repo `DaVinci Resolve MCP` (Samuel Gerski) e instalar `github/obra/superpowers` en Claude Code.
2. Estrategia de tokens: Opus (esfuerzo alto) para planificar la timeline; Sonnet para la ejecución de cortes.
3. Prompts de referencia:
```text
Hey, I'm starting a new project called 'AI_Edit'. Here is the file path to the raw footage: [PATH] and the script: [PATH/NOTION_URL]. Open DaVinci Resolve, create a timeline at 29.97 fps, import the clips, and create a rough cut matching the script.
```
```text
Find the pink clip in the timeline and move it to the location of the cream-colored marker. Collapse the gap and remove all red markers. Mark all remaining dead spaces with red markers for my manual review.
```

## CapCut (Python bridge / escritura directa de .draft)
- Requiere CapCut de escritorio instalado (Mac/PC). Claude escribe los archivos del proyecto sin abrir CapCut.
- Esta parte es de Gonzalo (`src/nle_bridge/capcut_exporter.py`). Prompt de referencia (Matt Loui):
```text
Edit my CapCut project named 'Emu War 3'. Perfectly sync the visual assets in '/assets/images/' to the voiceover audio in '/assets/audio/voice.mp3'. Add subtle zoom ins and zoom outs using keyframes for each image. Add sound effects from '/assets/sfx/' and background music at -22 dB. Add relevant text ensuring it stays within the 9:16 safe zones.

DO NOT USE COMPUTER USE OR OPEN CAPCUT. Build the timeline by writing the project files directly through file access to my Mac/PC.
```

## Blotato MCP (publicación)
1. Obtener la clave API desde el panel de Blotato. **No la pegues en el repo ni en chats**; guárdala en `.env` (ya ignorado por Git).
2. Instalar según Blotato: `npx skills add blotato-mcp` (o el cURL que ellos indiquen).
3. Prompt de referencia (siempre con aprobación humana del caption):
```text
Schedule the rendered motion graphics video for Instagram Reels, TikTok, and YouTube Shorts 30 minutes from now using Blotato MCP. Draft a viral caption, include relevant hashtags based on 'claude.md', and await my approval on the caption before finalizing the post.
```

## Control de calidad
Ver `.claude/skills/qc-loop/SKILL.md` y los sub-agentes en `.claude/agents/`.
