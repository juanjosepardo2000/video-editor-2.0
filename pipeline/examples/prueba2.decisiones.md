# Informe de decisiones: `prueba2.mp4` con `perfil-1`

Video: noticia de GTA 6, 62.4 s originales, **50.0 s tras el corte** (13 pausas de 0.5 a 2.3 s eliminadas, 162 de 162 palabras conservadas).

| Beat | Tiempo | Recurso | Motivo |
|---|---|---|---|
| 1 | 0.0 a 1.5 | `[interludio]` «GTA 6» a pantalla completa | **Hook** en el primer segundo: el título de la noticia en texto grande, con `hit` |
| 2 | 1.5 a 4.87 | `[hablante]` con punch-in | Se retoma al hablante tras el interludio; subtítulo grande en «cambiarlo» |
| 3 | 4.87 a 6.9 | `[tarjeta]` «Nuevo trailer» | Primera mención del trailer; tarjeta pequeña con `pop` |
| 4 | 6.9 a 10.95 | `[hablante]` plano abierto | Descanso visual; subtítulo en «Bay City.» |
| 5 | 10.95 a 13.0 | `[tarjeta]` «Jason y Lucía» | Nombres de los protagonistas |
| 6 | 13.0 a 17.09 | `[hablante]` con punch-in | Tramo largo sin gráfico: se varía el encuadre |
| 7 | 17.09 a 20.0 | `[broll]` `stock:criminal investigation board` | «Conspiración criminal» es un concepto que no se ve; reemplaza al hablante |
| 8 | 20.0 a 22.7 | `[hablante]` plano abierto | Descanso tras el B-roll |
| 9 | 22.7 a 25.64 | `[hablante]` con punch-in | Frase de transición |
| 10 | 25.64 a 28.98 | `[broll]` `stock:miami beach skyline aerial` | «Mundo abierto» y la ciudad; reemplaza al hablante |
| 11 | 28.98 a 31.0 | `[hablante]` plano abierto | Descanso tras el B-roll |
| 12 | 31.0 a 34.08 | `[cifra]` «19 de noviembre» | **Fecha**: dato clave de la noticia |
| 13 | 34.08 a 37.4 | `[hablante]` plano abierto | Las plataformas se leen en subtítulos (se respeta la separación entre gráficos) |
| 14 | 37.4 a 40.7 | `[contador]` «13 años» | **Cifra**: contador animado de 0 a 13 |
| 15 | 40.7 a 42.4 | `[hablante]` con punch-in | Antes de la pregunta central |
| 16 | 42.4 a 46.6 | `[titular]` «Superar todas las expectativas» | La pregunta que da sentido al video; tarjeta pequeña |
| 17 | 46.6 a 50.0 | `[hablante]` con `hit` | Cierre limpio con la invitación a comentar (está en lo dicho; no se inventó) |

## Comprobación de reglas (`perfil-1`)
- **Hook en el primer segundo:** cumple (interludio «GTA 6» a pantalla completa).
- **Cobertura de gráficos:** **45%** frente al objetivo de 35% (±10): cumple, **en el límite superior**.
- **Separación entre gráficos:** mínima 1.7 s (mínimo 1.5 s): cumple.
- **Gráficos simultáneos:** 1 a la vez: cumple.
- **Variedad:** 2 etiquetas seguidas como máximo: cumple.
- **Duración de beats:** de 1.5 a 4.2 s, con 3 beats fuera de 2 a 4 s (1.5 s el hook, 1.7 s, 4.1 s y 4.2 s): aceptable.
- **B-roll:** 2 beats, 12% del tiempo, ambos Pexels (sin IA ni créditos); el segundo concepto usa una ciudad costera genérica, no una imagen del juego.
- **Caption literal y texto en pantalla:** todo sale de lo dicho.
- **SFX:** 10.8 por minuto (9 en total).

## Límites y avisos
- La transcripción tiene errores evidentes que no se corrigieron por no inventar: «estado de la unidad» (probablemente «unión»), «demuestra de un golpe» (posible «un golpe que sale mal…»). Conviene que Juan las confirme escuchando el audio.
- Todavía **no hay detector de rostro**: las tarjetas pequeñas (beats 3, 5 y 16) pueden quedar cerca de la cara. Los interludios y el B-roll reemplazan al hablante, así que no la tapan.
- El B-roll de Pexels aún no está integrado como escena nativa (tareas C4 y G4): en el render aparece como pantalla de relleno hasta entonces.
- El corte actual no conserva pausas naturales (`keepPauseSec`, tarea C2): las pausas de más de 0.5 s se eliminan por completo.
