# Streamlit Community Cloud

!!! warning "Esqueleto — aún sin escribir"
    Esta página es un marcador de posición. El esquema de abajo es lo que
    cubrirá.

## Esquema

- Qué es: alojamiento gratuito que ejecuta una aplicación Streamlit directamente
  desde un repositorio público de GitHub.
- Conectar el repositorio, elegir la rama y el script de entrada.
- Dependencias: `requirements.txt`, y por qué las dependencias de la aplicación
  no son las de la librería.
- Cada push a la rama vuelve a desplegar. Dónde leer el registro de construcción
  cuando falla.
- Secretos y configuración, sin subirlos al repositorio.
- Los límites que importan: la aplicación se duerme cuando nadie la usa, los
  recursos están limitados y la URL no es tuya.
- Cuándo mudarse a otro sitio.

## Adónde ir después

- [Web estática](../static-web/index.md) — el camino sin servidor que se duerma.
- [GitHub Actions](../../github/actions.md) — automatizar las comprobaciones que
  se ejecutan antes de un despliegue.
