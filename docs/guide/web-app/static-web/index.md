# Web estática

Un sitio **estático** es una carpeta de archivos — HTML, CSS, JavaScript,
imágenes, JSON — que un host reparte sin tocarlos. No se ejecuta nada en el
servidor, porque prácticamente no hay servidor.

Suena limitado hasta que te fijas en cuánto cabe ahí dentro. Todo lo interactivo
sigue funcionando; simplemente se ejecuta en el navegador de quien visita. La
página del juego de este repositorio es estática, y ejecuta el **Python real**
del proyecto mediante [Pyodide](pyodide.md).

<div class="grid cards" markdown>

- [**HTML, CSS y JavaScript**](html-js.md) — los tres archivos de los que se
  compone una página web, y lo mínimo que hay que saber de cada uno.
- [**Python en el navegador**](pyodide.md) — ejecutar tu propio paquete en el
  cliente con Pyodide, para no escribir la lógica dos veces.

</div>

## Publicarla

Un sitio estático necesita un host estático, y el que viene con tu repositorio es
gratis: **[GitHub Pages](../../github/pages.md)**. Esa página cubre la rama
`gh-pages`, el flujo de despliegue y la URL publicada.

## Adónde ir después

- [GitHub Pages](../../github/pages.md) — publicar esto, gratis.
- [Streamlit](../streamlit/index.md) — el otro camino, si prefieres no escribir
  nada de JavaScript.
- [La página web](../../../game/advanced/web.md) — la aplicación estática de este
  repositorio, documentada de principio a fin.
