# Python en el navegador

!!! warning "Esqueleto — aún sin escribir"
    Esta página es un marcador de posición. El esquema de abajo es lo que
    cubrirá.

## Esquema

- Qué es [Pyodide](https://pyodide.org): CPython compilado a WebAssembly, cargado
  desde un CDN y ejecutándose dentro de la pestaña.
- Por qué importa: tu librería se ejecuta **tal y como está escrita**. Sin una
  segunda implementación en JavaScript que mantener sincronizada.
- Cargarlo, y el coste de la primera carga que paga quien visita.
- Meter tu propio paquete: empaquetar `src/` en un `.zip` que la página
  descomprime.
- La frontera Python ↔ JavaScript. Mantenla estrecha y pasa JSON por ella.
- No congelar la página: el bucle de eventos, y qué le hace un Python que tarda.
- Límites: sin hilos, sin sockets, sin sistema de archivos.

## Adónde ir después

- [La página web](../../../game/advanced/web.md) — este repositorio haciendo
  exactamente esto, documentado por completo.
- [GitHub Pages](../../github/pages.md) — publicar el resultado.
