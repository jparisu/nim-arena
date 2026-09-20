# Streamlit

**Streamlit** convierte un script de Python en una aplicación web. Sin HTML, sin
JavaScript, sin framework de front-end — escribes Python y él dibuja los widgets.

El precio es que **no es estática**: una aplicación Streamlit necesita un proceso
ejecutándose en algún sitio que responda a cada interacción. Eso es lo que
proporciona [Streamlit Community Cloud](cloud.md), gratis y con límites.

---

## Cómo funciona, en una línea

```mermaid
flowchart LR
    C["🖱️ Un clic"] --> S["🔁 Streamlit reejecuta<br/>tu script entero"]
    S --> W["🧩 Redibuja los widgets"]
```

Esa reejecución es lo único raro de Streamlit, y es lo primero que explica
[Construir la aplicación](building.md).

---

## Las páginas

<div class="grid cards" markdown>

- :material-application-braces-outline:{ .lg .middle } **[Construir la aplicación](building.md)**

    ---

    El script, los widgets y el modelo de estado.

- :material-cloud-upload-outline:{ .lg .middle } **[Streamlit Community Cloud](cloud.md)**

    ---

    Desplegarla desde tu repositorio, y los límites del plan gratuito.

</div>

---

**Siguiente:** [Web estática](../static-web/index.md) — el otro camino, sin servidor alguno.

**También:** [Alojamiento](../hosting.md)
