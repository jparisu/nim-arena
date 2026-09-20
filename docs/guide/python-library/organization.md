# Organización

Una librería es más que su código fuente: necesita un puñado de archivos que le
digan a Python (y a `pip`) cómo construirla, instalarla y describirla. Esta
página recorre la estructura que usa este repositorio y el propósito de cada
archivo, para que puedas reproducirla en tu propio proyecto.

---

## Estructura recomendada

Este proyecto usa la **estructura `src/`**, la buena práctica actual para
paquetes de Python:

```text
nim-arena/
├── src/
│   └── nimarena/          # el paquete en sí
│       ├── __init__.py    # la API pública: reexportaciones y __all__
│       ├── game.py        # reglas puras
│       ├── player.py      # la clase abstracta Player
│       ├── bots/          # un subpaquete por área funcional
│       │   ├── __init__.py
│       │   └── minimax.py
│       └── py.typed       # marca el paquete como tipado
└── tests/                 # scripts de prueba de la librería
    ├── test_game.py       # un módulo de pruebas por módulo de código
    ├── test_players.py
    └── ...

# Otros archivos y directorios auxiliares
├── pyproject.toml         # metadatos del proyecto y configuración de construcción
├── conftest.py            # configuración de rutas para pytest
├── README.md              # portada
├── LICENSE                # texto de la licencia
├── mkdocs.yml             # configuración de la documentación
├── docs/                  # la documentación que estás leyendo
├── players/               # jugadores enchufables, descubiertos vía players.yaml
├── web/                   # el sitio estático
├── scripts/               # ayudantes de construcción
├── .github/workflows/     # integración continua
```

Fíjate en el emparejamiento: `game.py` en `src/`, `test_game.py` en `tests/`.
Escala sin pensar: una función nueva es un módulo nuevo y un módulo de pruebas
nuevo.

Cuando una funcionalidad crece más allá de un solo módulo se convierte en un
**subpaquete**: un directorio con su propio `__init__.py` que reexporta los
nombres públicos de esa funcionalidad. `bots/` es uno — cinco módulos de
estrategia, de los cuales `__init__.py` solo reexporta las clases pensadas para
heredarse. Quien la use escribe `from nimarena.bots import MinimaxBot` y nunca
llega a saber en qué archivo vive.

El rasgo distintivo es que el paquete importable vive bajo `src/`, no en la raíz
del repositorio. La razón es sutil pero importante — véase
[La estructura `src/`](#the-src-layout) más abajo.

---

## Los archivos que importan

De todo el árbol de arriba, estos son los que hacen el trabajo:

| Archivo | Qué hace | ¿Obligatorio? |
|---|---|---|
| [`pyproject.toml`](#pyprojecttoml) | metadatos, dependencias y cómo se construye | ✅ sí |
| [`__init__.py`](#__init__py) | marca el paquete y define su API pública | ✅ sí |
| [`src/`](#the-src-layout) | dónde vive el paquete, y por qué no en la raíz | ✅ muy recomendable |
| [`py.typed`](#pytyped) | avisa de que el paquete trae anotaciones de tipo | ⬜ si anotas |
| [`tests/`](#tests-un-espejo-del-codigo) | un módulo de pruebas por módulo de código | ✅ sí |
| [`conftest.py`](#conftestpy) | configuración de rutas para pytest | ⬜ a veces |
| [`requirements.txt`](#requirementstxt) | fijar versiones de un despliegue | ⬜ rara vez |

### `pyproject.toml`

Este único archivo describe todo el proyecto: sus **metadatos** (nombre, versión,
descripción), sus **dependencias** y cómo se **construye**. Es el sustituto
moderno y estandarizado del antiguo `setup.py`. Estas son las partes clave del
archivo de este proyecto:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "nimarena"
version = "0.1.0"
description = "Parametrized NIM: a game engine, four reference AIs, a tournament runner, and a clean player API."
requires-python = ">=3.10"
license = "MIT"
dependencies = ["PyYAML>=6.0"]          # la única dependencia en ejecución

[project.optional-dependencies]
dev  = ["pytest>=7.0", "ruff>=0.4", "mypy>=1.11", "types-PyYAML"]
docs = ["mkdocs>=1.6", "mkdocs-material>=9.5", "mkdocstrings[python]>=0.25",
        "mkdocs-static-i18n>=1.2"]

[project.scripts]
nim-tournament = "nimarena.tournament:main"

[tool.hatch.build.targets.wheel]
packages = ["src/nimarena"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Cuatro partes merecen entenderse:

- **`[project]`** — la identidad de la librería. `name` es lo que la gente hace
  `pip install`; `version` es lo que fija; `dependencies` es lo que se instala
  *con* ella. Mantén esa lista tan corta como puedas: cada dependencia es algo
  que puede romperse, y algo que quien contribuya tiene que instalar.
- **`[project.optional-dependencies]`** — *extras*, instalados a demanda.
  `.[dev]` añade las herramientas de prueba y linter; `.[docs]` añade el conjunto
  de MkDocs. Quien use la librería no necesita ninguno; quien la desarrolla, sí.
- **`[project.scripts]`** — puntos de entrada de consola. Esta única línea es lo
  que convierte `nim-tournament` en un comando real de tu `PATH` tras la
  instalación, conectado a la función `main()` de `nimarena.tournament`.
- **`[tool.*]`** — configuración de otras herramientas en un solo sitio, en lugar
  de un `.flake8`, un `.mypy.ini` y un `pytest.ini` ensuciando la raíz.

!!! note "La configuración real lleva sus razones"
    El bloque `[tool.mypy]` de este proyecto son tres líneas de ajustes y ocho de
    comentario, explicando que sin `explicit_package_bases` el archivo
    `players/random.py` se convierte en el módulo `random` y **oculta la librería
    estándar** — de modo que cada `import random` del paquete resolvía a una clase
    de jugador. La configuración que te sorprendió una vez sorprenderá a la
    siguiente persona; deja escrito por qué está ahí.

### `__init__.py`

Un archivo `__init__.py` marca un directorio como **paquete regular**. Desde
Python 3.3 una carpeta sin él todavía puede importarse, como *paquete de espacio
de nombres*, pero una librería debería ser explícita: el archivo se ejecuta la
primera vez que se importa el paquete y define su **superficie pública**. El de
este proyecto, recortado:

```python
"""NIM Arena — a parametrized NIM engine, a clean player API, reference AIs,
and a robust round-robin tournament."""

from . import game
from .player import Player
from .registry import REGISTRY, Registry

__all__ = ["game", "Player", "Registry", "REGISTRY", "__version__"]
__version__ = "0.1.0"
```

Cinco nombres, elegidos deliberadamente. Todo lo demás —las tripas del torneo, el
cargador del manifiesto, los bots individuales— es alcanzable por su ruta
completa pero no forma parte de lo que el paquete anuncia. Esa distinción es el
tema de [API](api.md).

### `src/` — por qué el código no está en la raíz {#the-src-layout}

Colocar el paquete bajo `src/` evita un error clásico y confuso. Si el paquete
estuviera en la raíz del repositorio, ejecutar Python *desde* la raíz importaría
la carpeta local directamente, aunque la librería nunca se hubiera instalado. Las
pruebas pasarían contra el código en bruto mientras que la copia instalada de un
usuario real se comporta de otra forma.

Con la estructura `src/`, la raíz *no* es importable, así que estás obligado a
**instalar el paquete** (`pip install -e .`) antes de importarlo. Tus pruebas
corren entonces contra la librería exactamente tal y como la recibiría un
usuario. Es un paso extra que elimina toda una categoría de problemas del tipo
"en mi máquina funciona".

### `py.typed`

Un archivo vacío junto a `__init__.py`. Su presencia le dice a los comprobadores
de tipos que el paquete trae anotaciones de verdad y que deben confiar en ellas,
en lugar de tratar cada importación suya como `Any`. Si anotas tu código, añade
este archivo — sin él, tus usuarios no obtienen ningún beneficio.

### `tests/` — un espejo del código

La carpeta `tests/` contiene la batería de pruebas, separada del código que se
distribuye para que las pruebas no se instalen a los usuarios finales. Refleja lo
que prueba:
[`test_game.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_game.py)
cubre las reglas,
[`test_players.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_players.py)
cubre el contrato de jugador y
[`test_tournament.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_tournament.py)
cubre el ejecutor. Las pruebas tienen su propia página: [Tests](testing.md).

### `conftest.py`

Un archivo que pytest importa automáticamente antes de recolectar las pruebas. Es
donde viven los *fixtures* comunes, y donde se ajusta `sys.path` cuando parte del
proyecto no es un paquete instalado — aquí, la raíz del repositorio (para que
`players/` sea importable) y `web/` (para que lo sea el puente del navegador).

### `requirements.txt`

En muchos casos este archivo se usa como una lista simple de dependencias, una
por línea, tradicionalmente con `pip install -r requirements.txt`. Es un sistema
tradicional por compatibilidad, pero es redundante con `pyproject.toml`, que ya
contiene la lista de dependencias y sus versiones. Este proyecto no tiene uno.

---

## Versionado

La versión de la librería se declara como `version` en `pyproject.toml` y se
refleja en `__version__` dentro de `__init__.py`, de modo que se puede leer en
ejecución:

```python
>>> import nimarena
>>> nimarena.__version__
'0.1.0'
```

Los números siguen el **versionado semántico**, `MAYOR.MENOR.PARCHE`:

- **PARCHE** (`0.1.0 → 0.1.1`) — correcciones compatibles hacia atrás.
- **MENOR** (`0.1.0 → 0.2.0`) — funcionalidades nuevas, aún compatibles.
- **MAYOR** (`0.1.0 → 1.0.0`) — cambios que rompen la API existente.

Para publicar una versión nueva, sube el número (en los dos sitios) y fusiónalo
mediante el [flujo habitual de pull request](../github/pull-requests.md).

---

**Siguiente:** [Instalación y uso](installation-and-usage.md) — instala este paquete e impórtalo.

**También:** [API](api.md)
