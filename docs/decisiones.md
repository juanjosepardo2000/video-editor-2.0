# Decisiones del proyecto

Contradicciones entre los creadores (NotebookLM) y lo que elegimos. Cambiar una decisión = actualizar este archivo.

| # | Tema | Opciones en las fuentes | Decisión | Por qué |
|---|---|---|---|---|
| 1 | Dónde hacer el rough cut | Todo en Claude Code (Duncan, Joseph, Zinho) vs. herramienta dedicada (Descript, Glink, Fish Audio) | Script local de Carlos (WhisperX + FFmpeg). Descript MCP como plan B | Es el reparto del equipo; corre en local y sin costo por minuto |
| 2 | Opus vs. Sonnet | Opus para todo vs. Sonnet con buena Skill | Opus solo para planear el beat map; Sonnet para construir y revisar | Ahorra cuota en Claude Pro; las fuentes dicen que el código resultante es equivalente con buenas Skills |
| 3 | Render | Solo código (Remotion a MP4) vs. exportar a NLE | Híbrido: Remotion para overlays con fondo transparente y exportación a CapCut | Deja un proyecto editable para retoques finales |
| 4 | B-roll IA | Higgsfield vs. assets propios | Assets propios primero; Higgsfield solo para conceptos que no existan | Evita "AI slop" y gasto de créditos |

## Datos que siguen sin resolver
- Medidas de zonas seguras 9:16 en píxeles (nuestros valores son provisionales).
- Precio y límites de Blotato; créditos del plan gratuito y del de $19 de Higgsfield.
- Comando literal de FFmpeg del tutorial (usamos uno propio).

## 5 videos clave
1. Duncan Rogoff, "I Finally Solved AI Video Editing!" (~04:10 a 04:25): QC loop, 10 fps, 6 errores.
2. Joseph, "How to Edit VIRAL Instagram Reels Using Opus 5.5!" (~01:00 a 03:00): guía visual, 4 tipos de escena, beat map.
3. Matt Loui, "Claude + CapCut Completely Changes Everything For Editors" (~00:00 a 02:30): Remotion y .draft de CapCut.
4. AI Foundations (Drake), "FULL Claude + Higgsfield Tutorial" (~16:00 a 17:30): carpeta de contexto (ahora profiles/) y voz.
5. Alwi Batarilan, "Higgsfield MCP + Claude Is A Credit Trap" (~00:15 a 02:30): permisos y anti credit trap.

## Decisiones de producto (2026-10)
- **Modelo de uso:** consultoría que entrega la herramienta a empresas; la empresa elige un perfil de edición y paga sus propias APIs.
- **Demo/MVP:** se usan nuestras claves; en el MVP se añade una pantalla para que cada empresa pegue sus claves (guardadas localmente, nunca en el repo).
- **Entrega:** desktop primero (Remotion renderiza en local y el export a CapCut escribe archivos locales); versión online después, con render en la nube.
- **Licencias (música, fuentes como CoolVetica):** se revisan después de que el flujo funcione.
