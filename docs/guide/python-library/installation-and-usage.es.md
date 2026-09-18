# Instalación y uso

Una vez que una librería está empaquetada ([Organización](organization.md)),
usarla está a un `pip install` de distancia. Como la mayor parte del trabajo de
este curso ocurre en **notebooks (Google Colab)**, la vía principal es instalar
directamente desde GitHub — sin configuración local, sin clonar a mano.

## Instalar desde GitHub

!!! warning
    A la hora de instalar una librería en local, conviene usar entornos virtuales, sobre todo con librerías en desarrollo.
    Esto evita que nuestra librería pase a estar instalada en el sistema, o que se mezclen dependencias de distintas librerías.
    Lee [Instalar en local](#instalar-en-local) para más información.

`pip` puede instalar un paquete directamente desde un repositorio Git. Es la forma
más rápida de meter `nimarena` en un notebook mientras la librería todavía se
mueve:

```bash
pip install git+https://github.com/jparisu/nim-arena.git
```

Esto clona el repositorio entre bastidores, construye el paquete a partir de su
`pyproject.toml` y lo instala — exactamente como si viniera del Python Package
Index.

Puedes fijar una **rama**, etiqueta o commit concretos añadiendo `@<ref>`:

```bash
pip install git+https://github.com/jparisu/nim-arena.git@main
pip install git+https://github.com/jparisu/nim-arena.git@a9d292d
```

!!! tip "¿Por qué instalar desde GitHub?"
    Mientras una librería está en desarrollo activo y aún no se ha publicado en
    PyPI, instalar desde GitHub significa que todos obtienen siempre el código más
    reciente de una rama elegida, con un solo comando y sin pasos manuales. Encaja
    de forma natural con un flujo de trabajo basado en notebooks.

## Usarlo en un notebook

En un notebook de Colab, instala en una celda (el `!` inicial ejecuta un comando de
shell), luego importa y usa la librería:

```python
!pip install git+https://github.com/jparisu/nim-arena.git
```

```python
from nimarena import game
from nimarena.manifest import load_players

registry = load_players()            # lee players.yaml
hard = registry.get("hard")

state = [3, 5, 7]
print(hard.choose_move(state))       # p. ej. (0, 2)
print(game.nim_sum(state))           # 1
```

!!! note "Reinicia el entorno de ejecución tras instalar"
    Si ya habías importado `nimarena` en un notebook y luego instalas una nueva
    versión, reinicia el entorno de ejecución (**Runtime → Restart**) para que se
    cargue el código nuevo. Python cachea los módulos importados durante toda la
    sesión.

## Instalar en local

Para desarrollar la librería en sí —en lugar de solo usarla— instálala **en
local** en un entorno virtual. Un entorno virtual es una instalación de Python
aislada para un proyecto, de modo que sus dependencias no choquen con nada más de
tu máquina:

```bash
python -m venv .venv          # crea el entorno
source .venv/bin/activate     # actívalo (Windows: .venv\Scripts\activate)
pip install -e ".[dev]"       # instalación editable, con el extra dev
```

Dos opciones hacen de esto una instalación de *desarrollo*:

- **`-e` (editable).** El paquete se instala como un enlace a tu código fuente, de
  modo que tus ediciones surten efecto de inmediato — sin reinstalar tras cada
  cambio.
- **`.[dev]`** instala el paquete *más* su extra `test` (`pytest`, `ruff`, `mypy`), para que
  puedas ejecutar la suite enseguida (véase [Pruebas](testing.md)). Usa `.[docs]`
  para trabajar en la documentación en su lugar.

Esto es exactamente lo que hace el [workflow `tests.yml`](../github/actions.md#ejecutar-las-pruebas)
en CI, así que una ejecución verde en local significa una ejecución verde en
GitHub.

La instalación también deja el script de consola del proyecto en tu `PATH`,
gracias a `[project.scripts]` en `pyproject.toml`:

```bash
nim-tournament --no-subprocess --repetitions 1
```

## Adónde ir después

- [API](api.md) — cómo debería ser una interfaz pública limpia para la librería.
- [Pruebas](testing.md) — ejecuta y escribe la suite de pruebas.
