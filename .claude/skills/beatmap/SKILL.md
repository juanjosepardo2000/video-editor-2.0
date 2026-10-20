---
name: beatmap
description: Construye pipeline/beatmap.md a partir de pipeline/transcript.json. Asigna tipo de escena, visual, transición, SFX y caption por frase, y obtiene la aprobación del usuario antes de renderizar gráficos.
---

# Beat map

Entrada: `pipeline/transcript.json`, `claude.md`, perfil activo (`profiles/ACTIVE` y `profiles/<activo>/`). Salida: `pipeline/beatmap.md` (formato definido en ese archivo; no cambies sus columnas).

## Proceso
1. Un beat es cada frase hablada junto con lo que debe verse en pantalla mientras se dice (definición de Duncan Rogoff: "a beat map is a list of every sentence you say and what should be on screen while you say it"). Agrupa las palabras en frases y crea un beat por frase, con inicio/fin tomados del transcript.
2. Asigna a cada beat un tipo de escena:
   - `CAPTIONS`: hook inicial (mostrar la cara genera confianza) y frases conversacionales o de enlace.
   - `CAPTION_UI`: listas numeradas, llamados de atención o títulos de capítulo, sin tapar el rostro.
   - `SPLIT`: reglas, principios o comparaciones donde se ve el concepto y la cara a la vez.
   - `FULLSCREEN`: explicaciones conceptuales complejas, diagramas, listas de logos o momentos de alto impacto.
3. Describe el visual concreto (elemento en pantalla, foco de cámara, assets necesarios; es una instrucción interna que nunca se imprime), el **texto en pantalla** (único copy visible en tarjetas y gráficos; solo puede salir de lo dicho en `Speech` o del perfil activo, `-` si no aplica), la transición y el caption (1 a 3 palabras literales de `Speech` en acento).
   Contrato v2 (aprobado, con transición v1 y v2): después de `Texto en pantalla` van `B-roll` (`-`, `own:archivo`, `stock:palabras`, `ai:prompt`) y `Zona` (`arriba`, `abajo`, `lado`, `auto`), y el encabezado lleva `Contrato: v2`. Ejemplo: `pipeline/examples/beatmap.v2.example.md`. Hasta que el lector de Gonzalo acepte v2, el beat map que entra a Remotion se mantiene en v1.
   Columnas v1, en orden: `# | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | Transición | SFX | Caption`.
4. Asigna SFX según el vocabulario de `claude.md` sección 7.
5. Cadencia: un cambio visual cada ~1.5 a 3 s, ajustado al ritmo de la locución. No inventes datos que no estén en el transcript.
6. **Antes de escribir código gráfico**: muestra el beat map al usuario, haz preguntas aclaratorias ("ask me any clarifying questions": layout, colores, duración de animaciones) y, si lo pide, genera mockups. Iterar el plan en texto es barato; iterar animaciones renderizadas no.
7. Solo tras aprobación explícita, pasa a Gonzalo/Remotion con: "Here's the full plan, now use Remotion to build these animations".
8. Escribe `B-ROLL IA:` al inicio de la columna Visual en los beats que necesitan generación y usa la skill `higgsfield-budget` antes de generar.

## Prompt base (Joseph | Video Editing)
```text
This is the transcript of a short form video I'm editing. Use the short form editing skills, the brand guideline, and the content psychology to come up with the animations for this video. Use a light Apple theme with orange accent colors.
```
