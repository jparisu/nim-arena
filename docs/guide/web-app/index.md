# Aplicación web

!!! warning "Esqueleto — aún sin escribir"
    Solo existe la estructura de esta sección. Las páginas de abajo son
    marcadores de posición.

Una librería que nadie puede probar es una librería que nadie usa. Esta sección
trata de ponerle **cara** al proyecto: una página que alguien abre en el
navegador y usa, sin instalar nada.

Hay dos caminos, y no cuestan lo mismo. Lee primero
[Alojamiento](hosting.md) — explica qué implica de verdad la elección — y luego
escoge uno.

<div class="grid cards" markdown>

- [**1. Alojamiento**](hosting.md) — dónde se ejecuta una aplicación web, quién
  la paga y por qué «estática» es la palabra que decide todo lo demás.
- [**2. Streamlit**](streamlit/index.md) — escribe toda la aplicación en Python y
  despliégala en Streamlit Community Cloud.
- [**3. Web estática**](static-web/index.md) — HTML, CSS y JavaScript en una
  carpeta, publicados gratis desde tu repositorio.

</div>

## ¿Cuál elijo?

| | [Streamlit](streamlit/index.md) | [Web estática](static-web/index.md) |
| --- | --- | --- |
| Lenguaje | Solo Python | HTML, CSS, JavaScript (+ Python vía Pyodide) |
| Necesita servidor | Sí | No |
| Dónde se ejecuta | Streamlit Community Cloud | GitHub Pages, cualquier host estático |
| Se duerme si nadie la usa | Sí | No |
| Esfuerzo inicial | Bajo | Medio |

## Adónde ir después

- [GitHub Pages](../github/pages.md) — el host estático gratuito que usa este
  proyecto.
- [Documentación](../documentation/index.md) — el *otro* sitio que publica un
  proyecto, y por qué va aparte.
