# Streamlit Community Cloud

**Streamlit Community Cloud** ejecuta una aplicación Streamlit directamente
desde un repositorio público de GitHub, gratis, en una URL que cualquiera puede
abrir. Le señalas un repositorio, una rama y un script; él instala las
dependencias, arranca el proceso y lo mantiene en marcha.

Es el camino más corto entre "funciona en mi portátil" y "aquí tienes un
enlace".

## Desplegar

1. Entra en [share.streamlit.io](https://share.streamlit.io) **con tu cuenta de
   GitHub** y autorízalo a leer tus repositorios.
2. **New app → Deploy a public app from GitHub.**
3. Rellena tres campos:

    | Campo | Valor |
    | --- | --- |
    | **Repository** | `<tu-usuario>/<tu-proyecto>` |
    | **Branch** | `main` |
    | **Main file path** | `app.py` |

4. Opcionalmente reserva un subdominio — `tu-juego.streamlit.app` se lee mejor
   que el generado.
5. **Deploy.** La primera construcción tarda unos minutos, sobre todo
   instalando dependencias. El log sale en pantalla; léelo, porque es donde
   aparecen los fallos.

La aplicación es pública desde el momento en que se despliega. No hay un paso
de "publicar" aparte.

## Dependencias

El servicio instala **`requirements.txt` desde la raíz del repositorio**. No
`pyproject.toml`, ni tu lockfile, ni el entorno que tengas en local.

Ese archivo necesita Streamlit *y* tu propio paquete:

```text
streamlit>=1.36
git+https://github.com/<tu-usuario>/<tu-proyecto>@main
```

!!! warning "Las dependencias del despliegue no son las de la librería"
    Tu `pyproject.toml` lista lo que la *librería* necesita para poder
    importarse. `requirements.txt` lista lo que la *aplicación desplegada*
    necesita para arrancar. Streamlit va en el segundo y no en el primero: a
    quien instale tu paquete para escribir un bot no se le debe obligar a
    instalar un framework web.

Si tu paquete está en el mismo repositorio que la aplicación, instalarlo desde
Git parece redundante. No lo es: es lo que garantiza que la aplicación
desplegada importa el mismo paquete contra el que se ejecutan los tests, y no
lo que haya quedado junto a `app.py`. Mira
[Instalación y uso](../../python-library/installation-and-usage.md).

## Cada push vuelve a desplegar

Haz push a la rama que desplegaste y la aplicación se reinicia con el nuevo
commit. No hay nada que activar.

Eso es cómodo y es también la trampa: **un commit roto en `main` es una
aplicación pública rota, de inmediato.** La defensa es la que ya tienes:
protege `main`, exige que los tests pasen y fusiona a través de pull requests.
Mira
[Configuración del repositorio](../../github/repository-configuration.md).

!!! tip "Lee el log antes de adivinar"
    **Manage app** (abajo a la derecha, en tu propia aplicación) abre el log en
    marcha. Casi todo despliegue fallido es una de estas tres cosas, y el log
    dice cuál: un paquete que falta en `requirements.txt`, una versión de
    Python que no coincide, o una excepción al importar `app.py`.

## Configuración y secretos

Cualquier cosa que no deba estar en el repositorio —una clave de API, un
token— va en **Settings → Secrets**, en formato TOML, y llega a la aplicación a
través de `st.secrets`:

```toml
# pegado en Settings → Secrets, nunca commiteado
admin_token = "…"
```

```python
token = st.secrets["admin_token"]
```

Esta es una ventaja real frente a una [página estática](../static-web/index.md),
donde un secreto es imposible por construcción. Para un proyecto de juego
seguramente no necesites nada de esto — pero si te descubres queriendo uno, es
aquí donde va, y `.gitignore` es donde va `.streamlit/secrets.toml`.

## Los límites que te van a morder

| Límite | Lo que vas a notar |
| --- | --- |
| **La aplicación se duerme** | tras un rato sin visitas se apaga; la siguiente persona espera ~30 s a que despierte |
| **CPU y memoria limitadas** | una búsqueda profunda en un bot puede morir, no solo ir lenta |
| **Sin disco persistente** | lo que la aplicación escriba desaparece al reiniciar |
| **Un proceso, compartido** | dos visitantes son dos sesiones en un proceso; un bucle infinito en un bot se lleva a los dos por delante |
| **El dominio no es tuyo** | `*.streamlit.app`, y el proveedor puede retirar el proyecto |

!!! warning "Despiértala antes de una demostración"
    Una aplicación dormida es la forma más común de que un proyecto que
    funciona parezca roto delante de un público. Abre la URL unos minutos antes
    de presentar y deja la pestaña abierta.

De todos ellos, **no hay disco persistente** es el que cambia un diseño. Si tu
aplicación necesita recordar algo entre reinicios, no puede escribir un
archivo: haz commit de los datos al repositorio desde un
[workflow](../../github/actions.md) y que la aplicación los lea. Una
clasificación producida por CI y leída por la aplicación es la forma normal;
mira [El marcador](../../../game/advanced/scoreboard.md).

## Cuándo dejarlo

Tres señales, de menos a más grave:

- **La espera al despertar es inaceptable.** Entonces quieres algo estático,
  que nunca se duerme: [GitHub Pages](../../github/pages.md).
- **Estás peleándote con el límite de recursos.** Haz el trabajo caro en CI,
  publica el resultado y que la aplicación lo lea.
- **Necesitas un backend de verdad** — cuentas, base de datos compartida,
  multijugador en vivo. Eso es otro proyecto, y un plan gratuito no lo va a
  sostener.

Para un juego por turnos de dos jugadores con un bot como rival, ninguna de
estas debería llegar. El juego entero cabe cómodamente en un proceso gratuito,
o en el navegador de quien visita.

## Adónde ir después

- [Construir la aplicación](building.md) — el script que esto despliega.
- [Web estática](../static-web/index.md) — la ruta sin un servidor que se
  duerma.
- [Configuración del repositorio](../../github/repository-configuration.md) —
  evitar que un commit roto se convierta en una aplicación pública rota.
