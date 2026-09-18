# API

La **API** (interfaz de programación) de una librería es su *cara pública*: los
objetos, funciones y métodos que quien la usa debe tocar. Todo lo demás es un
detalle de implementación que eres libre de cambiar. Diseñar bien esa *cara* es
lo que separa una librería que da gusto usar de otra con la que se pelea.

!!! tip "La parte que ya existe"
    Todo lo que viene abajo está ilustrado con código real y en producción. La
    página de [API de jugador](../../arena/player-api.md) es el contrato público
    actual de `nimarena`, generado en parte a partir de sus docstrings. Lee esta
    página para el *porqué* de una API, y aquella para el *qué* ofrece hoy la
    librería.

## Qué es aquí una API

Piensa en una librería como algo con dos caras:

- la **API pública** — lo que la gente importa y llama, y lo que prometes
  mantener estable entre versiones;
- las **interioridades** — funciones auxiliares, módulos privados y estructuras
  de datos que la hacen funcionar, y que puedes reescribir cuando quieras.

El valor de la distinción es la libertad: mientras la API pública mantenga su
forma, puedes refactorizar todo lo que hay detrás sin romperle nada a nadie. El
primer trabajo del diseño de una API es, por tanto, **decidir qué es público** y
dejar esa frontera a la vista.

En Python, la frontera se dibuja por convención y con `__all__`:

- Los nombres con guion bajo delante (`_helper`, `_Cache`) son **privados** — una
  señal de que nadie debería depender de ellos.
- La lista `__all__` de un módulo nombra sus objetos **públicos**. Documenta la
  superficie prevista y controla qué trae `from nimarena import *`.

Así lo hace `nimarena`, con su API pública declarada explícitamente en
`__init__.py`:

```python
# src/nimarena/__init__.py
from . import game
from .player import Player
from .registry import REGISTRY, Registry

__all__ = ["game", "Player", "Registry", "REGISTRY", "__version__"]
__version__ = "0.1.0"
```

Cinco nombres. Quien la use escribe `from nimarena import Player` y nunca tiene
que saber en qué módulo vive — ni que el torneo, justo al lado, es un archivo de
1600 líneas lleno de bifurcación de procesos y contabilidad en memoria compartida
sobre el que no se le promete nada.

## Diseñar una API buena

Un puñado de principios hacen que una interfaz sea predecible y agradable:

- **Consistencia.** Las cosas parecidas deben parecerse. En `nimarena.game`,
  todas las funciones reciben el estado como primer argumento y ninguna lo muta:
  en cuanto has llamado a una, puedes predecir el resto.
- **Firmas pequeñas y predecibles.** Pocos parámetros, valores por defecto
  sensatos y ninguna sorpresa.
- **Nombres con significado.** `legal_moves`, `is_terminal`, `nim_sum` dicen lo
  que son. Evita abreviaturas que solo entiende quien las escribió.
- **Anotaciones de tipo.** Anota parámetros y valores de retorno. Documentan la
  interfaz, habilitan el autocompletado del editor y permiten que las
  herramientas cacen errores antes de ejecutar. Añade un archivo `py.typed` para
  que quien te use también se beneficie.
- **Docstrings.** Cada objeto público lleva un docstring corto que dice qué hace,
  qué recibe y qué devuelve.

```python
def apply_move(state: State, move: Move) -> State:
    """Return a **new** state with ``move`` applied.

    Args:
        state: the current board; never mutated.
        move: the ``(row, count)`` to apply.

    Returns:
        A new list of ints.

    Raises:
        ValueError: if the move is not legal from ``state``.
    """
```

Las anotaciones y el docstring juntos le dicen a quien lo lea todo lo que
necesita para llamar a `apply_move` correctamente, sin leer su cuerpo.

## Diseñar una API que otros implementan

Algunas librerías las llaman sus usuarios. Otras las **implementan** ellos: la
librería define una forma y quien la usa aporta el código que la rellena. Una
arena de juego es del segundo tipo — alguien de fuera escribe una clase y la
librería la ejecuta. Eso invierte el problema de diseño, y tres decisiones
cargan con casi todo el peso.

### Una clase base abstracta es un contrato que Python impone

```python
from abc import ABC, abstractmethod


class Player(ABC):
    @classmethod
    @abstractmethod
    def get_name(cls) -> str: ...

    @abstractmethod
    def choose_move(self, state: State) -> tuple[int, int]: ...
```

Heredar de `ABC` y marcar métodos con `@abstractmethod` hace que el propio Python
se niegue a construir una implementación incompleta:

```text
TypeError: Can't instantiate abstract class MyBot without an
           implementation for abstract method 'get_name'
```

Ese error llega en el momento del fallo y con el nombre del método que falta
dentro. Un `NotImplementedError` lanzado desde un método base llegaría más tarde,
desde otro sitio, en mitad de un torneo.

### Mantén el contrato tan pequeño como permita el trabajo

`Player` pide cuatro accesores de identidad y **un** método de juego. No hay,
deliberadamente, ni `on_game_start`, ni historial de jugadas, ni identidad del
rival, ni temporizador.

Cada parámetro de una interfaz es una cosa más que alguien de fuera puede
malinterpretar, y una cosa más que nunca podrás quitar. Las preocupaciones que
pertenecen a *quien llama* —control de tiempo, emparejamientos,
reproducibilidad— se quedan en quien llama. El resultado es un jugador que es una
función pura del tablero, que además es lo más fácil de probar.

### Pon la identidad en métodos de clase y la construcción tras una fábrica

```python
@classmethod
def get_name(cls) -> str: ...

@classmethod
def create(cls, seed: int) -> "Player":
    return cls()
```

Las dos elecciones existen por lo que necesita *quien llama*:

- **La identidad como método de clase** permite al torneo, a la documentación y a
  la página web etiquetar a un jugador **sin construir uno**. Crear un objeto solo
  para preguntarle su nombre es un coste sorprendente y un modo de fallo
  sorprendente.
- **Una fábrica `create(seed)`** le da a quien llama una única vía de
  construcción uniforme. La alternativa —un parámetro `seed` en cada `__init__`—
  mete una preocupación del torneo en la firma que tiene que escribir cada autor,
  y obliga a quien llama a inspeccionar firmas para averiguar qué clase acepta
  qué. La implementación por defecto ignora la semilla, así que un bot
  determinista no escribe nada.

### Descubrimiento: una lista explícita gana a un escaneo de carpeta

`nimarena` encuentra jugadores mediante un único archivo editado a mano:

```yaml
players:
  - file: hard.py
    class: Hard
```

Escanear `players/*.py` habría sido escribir menos. También habría significado
**ejecutar el código de nivel superior de un desconocido solo para descubrirlo**,
y habría ocultado qué se está admitiendo. Con un manifiesto, quien revisa ve el
archivo nuevo y la única línea que lo admite en un mismo diff — la frontera de
confianza es la revisión, y la revisión es visible.

Fíjate también en lo que el manifiesto *no* contiene: el nombre, los autores y la
descripción del jugador. Eso viene de la clase, porque duplicarlo aquí daría dos
fuentes de verdad y una de las dos acabaría desviándose.

!!! tip "La regla general"
    Cuando una decisión de diseño no sea obvia, deja escrito el *porqué* en el
    docstring del módulo. `nimarena/player.py` empieza con treinta líneas que
    explican exactamente las cuatro decisiones de arriba. A la siguiente persona
    que lo toque —muy posiblemente tú— no le hará falta volver a deducirlas.

## Documentar la API automáticamente

Una referencia de API escrita a mano se queda desfasada enseguida: alguien
renombra un parámetro y la página sigue mostrando el antiguo. La solución es
generar la página **a partir de los docstrings**, para que solo haya una copia de
la verdad.

[mkdocstrings](https://mkdocstrings.github.io/) hace eso en MkDocs. Una directiva
dentro de una página:

```markdown
::: nimarena.game
```

renderiza la firma, las anotaciones de tipo, la tabla de argumentos y los
ejemplos de cada objeto listado, con un enlace a las líneas de código de las que
salió. Así se construye la mitad inferior de
[Estructura del código](../../arena/code-structure.md) y de
[API de jugador](../../arena/player-api.md).

Dos hábitos hacen que la página generada merezca leerse:

- **Escribe los docstrings con un estilo consistente.** Este proyecto usa el
  estilo Google mostrado arriba (`Args:`, `Returns:`, `Raises:`), declarado una
  sola vez en `mkdocs.yml`.
- **Documenta el *porqué*, no la firma.** La firma ya está en la página. Lo que
  quien lee no puede ver es por qué existe el parámetro.

## Adónde ir después

- [API de jugador](../../arena/player-api.md) — las mismas ideas, aplicadas: el
  contrato público real de `nimarena`.
- [Tests](testing.md) — cómo verificar que la API se comporta como se diseñó.
- [MkDocs](../documentation/mkdocs.md) — configurar mkdocstrings.
