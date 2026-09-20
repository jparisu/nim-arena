# Documentación avanzada

Cómo está montado NIM Arena por dentro. **No** necesitas nada de esto para
escribir un bot — para eso ve a [Subir un bot nuevo](../upload-a-bot/index.md).

Léelo si quieres entender la maquinaria, arreglar un error o cambiar el proyecto
en sí.

<div class="grid cards" markdown>

- [**Estructura del código**](code-structure.md) — el árbol del repositorio y cómo
  dependen unos módulos de otros.
- [**El marcador**](scoreboard.md) — el archivo de resultados y cómo se renderiza.
- [**El torneo**](tournament.md) — formatos, presupuestos de tiempo y
  descalificaciones.
- [**La página web**](web.md) — la página Pyodide que ejecuta el mismo Python en
  tu navegador.
- [**Referencia de la API**](api.md) — todos los nombres públicos de `nimarena`,
  generados desde el código fuente.

</div>

## La idea central

> Las reglas del juego y todas las IA se escriben **una sola vez, en Python**. Ese
> mismo código ejecuta tanto el torneo evaluado (en CI) como el juego en vivo en
> el navegador (vía Pyodide). **Una única fuente de verdad.** Las reglas nunca se
> reimplementan en JavaScript.
