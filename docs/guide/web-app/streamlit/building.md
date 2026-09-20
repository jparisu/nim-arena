# Construir la aplicación

!!! warning "Esqueleto — aún sin escribir"
    Esta página es un marcador de posición. El esquema de abajo es lo que
    cubrirá.

## Esquema

- `pip install streamlit`, `streamlit run app.py` y el ciclo de recarga en vivo.
- El modelo de ejecución: el script entero se vuelve a ejecutar de arriba abajo
  en cada interacción. Todo lo demás se deduce de esto.
- Widgets: `st.button`, `st.slider`, `st.selectbox`, `st.text_input`.
- Maquetación: columnas, pestañas, la barra lateral, `st.container`.
- Conservar valores entre ejecuciones: `st.session_state`.
- No recalcular lo caro: `@st.cache_data`, `@st.cache_resource`.
- Llamar a *tu propia librería* desde la aplicación — la aplicación es una
  cáscara fina, la lógica se queda en el paquete.
- Estructura del proyecto: dónde va `app.py` y qué corresponde a
  `requirements.txt`.

## Adónde ir después

- [Streamlit Community Cloud](cloud.md) — ponerla en línea.
