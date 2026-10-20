# Guía de estilo: Perfil 1 (borrador con 5+5 referencias)

Confianza **baja**: pocas referencias y SFX sin medir. Cada regla indica su base (n = narrativo, v = visual; ver `references.md` y `metrics/resumen.json`).

## Resumen
Ritmo conversacional tipo Davo (el hablante manda, pocos cortes, pausas naturales) con **interludios gráficos a pantalla completa** y subtítulos palabra a palabra, a la manera de las ediciones profesionales de TikTok.

## Bloque narrativo (ritmo, hooks, cortes, momentos)
| Parámetro | Valor | Base |
|---|---|---|
| Duración típica de plano | ~14 s (3 a 24) | n1 a n5 |
| Cortes por minuto | ~3 (vlog hasta 16) | n1 a n5 |
| Palabras por minuto | 150 a 200 | n1, n2, n3, n5 (n4 excluido) |
| Hook | empieza a hablar en < 1 s | n1, n2, n3, n5 |
| Pausas | se conservan las naturales | n3, n5 (22 y 39 pausas > 0.3 s) |
| Momentos que se conservan | reacciones, risas, comentario en pantalla, stitch con otro video | n2, n5 (observado) |

## Bloque visual (subtítulos, tarjetas, zooms, SFX, composición 9:16)
| Parámetro | Valor | Base |
|---|---|---|
| Duración típica de plano | ~2.8 s (2 a 4.7) | v1 a v5 |
| Cortes por minuto | ~19 (11 a 30) | v1 a v5 |
| Música | continua; -14 a -22 LUFS (mediana -15.9) | v1 a v5 |
| Subtítulos | palabra a palabra, 1 a 3 palabras, a ~65% de la altura, palabra clave más grande o en color de acento | v1, v2, v3, v5 (observado) |
| Gráficos | interludios a pantalla completa que sustituyen al hablante, o recuadro pequeño con esquinas redondeadas | v1, v2, v4, v5 (observado) |
| Gráficos simultáneos | 1 a la vez | v1 a v5 (observado) |
| Zooms y transiciones | punch-in/out y cambios de escena (v3), desenfoque (v1) | observado |
| Tipografía | sans gruesa + acento serif cursiva o manuscrita para la palabra clave | v3, v4 (observado) |
| SFX | **por medir** | pendiente |

## Lo más importante para el compositor
**Nunca una tarjeta sobre la cara.** En las referencias, los gráficos sustituyen al hablante (pantalla completa) o son recuadros pequeños; los subtítulos van a la altura del pecho. Esto es lo que debe imitar la colocación automática.

## Advertencias
- Los picos reales de las referencias llegan a +3.4 dBFS (audio saturado): **no copiar**. Nuestro objetivo: pico real <= -1 dBFS.
- Porcentaje de pantalla con gráficos: estimado a ojo entre 15% y 60%; usamos 35% provisional.
- No se copian marcas, música, voz ni contenido de los creadores.

## Validación
- [ ] Comentarios de Juan por cada referencia (`references.md`)
- [ ] Medir SFX (densidad por minuto y tipos)
- [ ] Clip de prueba editado en este estilo y comparado lado a lado
- [ ] Aprobado por Juan (fecha: ____)
