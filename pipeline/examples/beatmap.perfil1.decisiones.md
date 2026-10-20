# Informe de decisiones: beat map propuesto con `perfil-1` para `prueba.mp4`

| Beat | Tiempo | Recurso | Motivo |
|---|---|---|---|
| 1 | 0.0 a 3.2 | `[hablante]` con palabra clave «test» | La frase de apertura es un saludo sin afirmación fuerte: no hay titular que mostrar; se da peso a la palabra clave con el subtítulo grande |
| 2 | 3.2 a 4.6 | `[tarjeta]` «Editor de vídeos» (CAPTION_UI) | Aparece el tema por primera vez; tarjeta pequeña con sonido `pop` |
| 3 | 4.6 a 8.3 | `[hablante]` con punch-in (`zoom-in`) | Tramo largo sin gráfico: se varía el encuadre y se evita la monotonía |
| 4 | 8.3 a 11.6 | `[broll]` FULLSCREEN, `stock:video editing software screen` | «El asistente de vídeos» es un concepto que no se ve en cámara; el B-roll reemplaza al hablante (no tapa la cara) |
| 5 | 11.6 a 14.9 | `[hablante]` sin gráficos | Descanso visual tras el B-roll; respeta la separación mínima entre gráficos |
| 6 | 14.9 a 16.1 | `[hablante]` con `hit` | Cierre limpio; no se inventa llamada a la acción porque no se dice |

## Comprobación de reglas (`perfil-1`)
- **Cobertura de gráficos:** 29% frente al objetivo de 35% (±10): cumple.
- **Separación entre gráficos:** 3.7 s frente al mínimo de 1.5 s: cumple.
- **Gráficos simultáneos:** 1: cumple.
- **Variedad de etiquetas:** `[hablante]` aparece 2 veces seguidas (beats 5 y 6, dos tramos de descanso); no es un gráfico, pero se anota.
- **Duración de beats:** 1.4 s (beat 2) y 1.2 s (beat 6, limitado por el final del video) frente al objetivo de 2 a 4 s: el beat 6 queda corto de forma inevitable.
- **Caption literal:** todas las palabras salen de `Speech`: cumple.
- **Texto en pantalla:** sale de lo dicho («editor de vídeos», «asistente de vídeos»): cumple.
- **B-roll:** 1 de 6 beats (20% del tiempo), sin IA ni créditos.

## Límites del material
- El video original **no tiene un hook fuerte** (empieza con un saludo y un titubeo). La regla del primer segundo con titular solo se cumple a medias con la palabra clave. Para una prueba más representativa conviene grabar una apertura con una afirmación o pregunta.
- La transcripción contiene un error evidente («conía»); por la regla de no inventar, no se corrigió.
- No hay cifras ni comparaciones: no se probaron `[contador]` ni `[comparacion]` (por eso conviene el video de prueba con cifras, tarea J5).
