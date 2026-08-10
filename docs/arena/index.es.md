# NIM Arena

El manual de referencia de este repositorio: qué contiene, cómo encajan las
piezas y cómo añadir un jugador propio.

Si lo que buscas es cómo construir un proyecto como este —Git, GitHub,
empaquetado, CI, documentación— esa es la otra mitad del sitio: la
[Guía del estudiante](../guide/index.md).

<div class="grid cards" markdown>

- [**Reglas del juego**](rules.md) — cómo funciona el NIM y la estrategia XOR que
  lo gana.
- [**Primeros pasos**](getting-started.md) — instalar, jugar, ejecutar las pruebas
  y el torneo.
- [**Estructura del código**](code-structure.md) — el árbol del repositorio y cómo
  dependen unos módulos de otros.
- [**API de jugador**](player-api.md) — la interfaz exacta que implementa cada IA.
- [**Enviar un jugador**](submit-a-player.md) — el flujo de pull request, paso a
  paso.
- [**El marcador**](scoreboard.md) — el archivo de resultados y cómo se renderiza.
- [**El torneo**](tournament.md) — formatos, presupuestos de tiempo y descalificaciones.
- [**La página web**](web.md) — la página Pyodide que ejecuta el mismo Python en
  tu navegador.

</div>

## La idea central

> Las reglas del juego y todas las IA se escriben **una sola vez, en Python**. Ese
> mismo código ejecuta tanto el torneo evaluado (en CI) como el juego en vivo en
> el navegador (vía Pyodide). **Una única fuente de verdad.** Las reglas nunca se
> reimplementan en JavaScript.

## El camino más corto hasta tu propio jugador

1. Lee las [reglas](rules.md) — cinco minutos.
2. [Instala](getting-started.md) el paquete.
3. Copia el ejemplo mínimo de la [API de jugador](player-api.md).
4. Añade una línea a `players.yaml` y [abre un PR](submit-a-player.md).
