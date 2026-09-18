# Pruebas

Las pruebas son código que comprueba tu código. Son lo que te permite cambiar una
librería con confianza: si un cambio rompe algo, una prueba lo detecta al
instante en lugar de que un usuario se entere más tarde. Esta página explica por
qué importan, cómo se organiza la carpeta `tests/`, cómo escribirlas y ejecutarlas
con **pytest**, y cómo se convierten en una puerta automática en cada pull request.

## Por qué pruebas unitarias

Una **prueba unitaria** ejercita una pieza pequeña de la librería de forma
aislada y afirma que se comporta como se espera. Su verdadero valor aflora con el
tiempo:

- **Detectan regresiones.** Cuando cambias la búsqueda de `minimax.py`, las
  pruebas te dicen al instante si has roto el oráculo de finales de encima.
- **Hacen segura la refactorización.** Puedes reescribir las entrañas de la
  [API](api.md) con libertad, porque una suite que pasa demuestra que el
  comportamiento público no ha cambiado.
- **Documentan el comportamiento.** Una prueba es un ejemplo ejecutable de cómo se
  supone que se llama a una función y qué debería devolver.
- **Habilitan la colaboración.** En un equipo, las pruebas son cómo confías en el
  pull request de un compañero sin releerlo entero — las comprobaciones están en
  verde.

El coste es pequeño y se paga una vez; el beneficio se acumula cada vez que el
código cambia.

## La estructura `tests/`

Las pruebas viven en una carpeta `tests/` de nivel superior, mantenida fuera del
paquete que se distribuye (véase [Organización](organization.md)). La suite
**refleja el código fuente**: cada parte de la librería tiene su archivo
`test_*.py` correspondiente, de modo que es obvio dónde vive una prueba y dónde
falta.

```text
tests/
├── test_game.py        # las reglas: jugadas legales, aplicar, final, nim-sum
├── test_players.py     # todo jugador admitido respeta el contrato
├── test_bots.py        # las estrategias de búsqueda reutilizables
├── test_manifest.py    # players.yaml se carga y se valida correctamente
├── test_tournament.py  # el ejecutor sobrevive a bots colgados, rotos y tramposos
└── test_web_*.py       # el puente del navegador y los recursos estáticos
```

`test_game.py` acompaña a `src/nimarena/game.py`, y `test_tournament.py` a
`src/nimarena/tournament.py`. Un módulo de código, un módulo de pruebas: ese
emparejamiento es toda la convención.

Dos convenciones de nombres permiten a pytest **descubrir** las pruebas
automáticamente, sin registro:

- los *archivos* de prueba se llaman `test_*.py`,
- las *funciones* de prueba se llaman `test_*`.

La forma más simple — llama a la cosa y afirma algo sobre ella:

```python
# tests/test_game.py
from nimarena.game import apply_move, is_terminal, nim_sum


def test_apply_move_does_not_mutate_the_input():
    state = [3, 5, 7]
    apply_move(state, (0, 2))
    assert state == [3, 5, 7]


def test_nim_sum_of_a_balanced_position_is_zero():
    assert nim_sum([2, 5, 7]) == 0
```

Cada función prueba un hecho, y su nombre dice cuál es — de modo que un informe
de fallo se lee como una frase:
`test_apply_move_does_not_mutate_the_input failed`.

## Escribir y ejecutar pruebas con `pytest`

[pytest](https://docs.pytest.org/) es el ejecutor de pruebas estándar de facto de
Python. Instálalo mediante el extra de pruebas y ejecuta toda la suite con una
palabra:

```bash
pip install -e ".[dev]"
pytest
```

!!! tip "Instala el paquete antes de probarlo"
    El paquete vive bajo `src/`, que Python no busca por defecto, así que un
    `pytest` a secas en un clon recién hecho falla con
    `No module named 'nimarena'`. La instalación editable (`pip install -e .`) es
    lo que lo pone en la ruta — y hace que las pruebas se ejecuten contra la
    librería exactamente como la recibe un usuario. Las partes del proyecto que
    *no* son paquetes instalados, como `players/` y `web/`, las pone en la ruta
    `conftest.py`.

```console
$ pytest -q
........................................................  [ 43%]
........................................................  [ 87%]
................                                          [100%]
128 passed in 21.43s
```

Las funciones del día a día que usarás:

- **Aserciones.** Simples sentencias `assert` — pytest las reescribe para mostrar
  los valores reales en caso de fallo, así que rara vez necesitas nada más.
- **Parametrización.** Ejecuta la misma prueba sobre muchas entradas con
  `@pytest.mark.parametrize`, en lugar de copiar y pegar. Este proyecto la usa
  para ejecutar las mismas comprobaciones sobre *cada* jugador admitido:

    ```python
    LADDER = ["random", "easy", "medium", "hard"]


    @pytest.mark.parametrize("name", LADDER)
    def test_every_player_declares_its_identity(name):
        cls = type(load_players().get(name))
        assert cls.get_name() == name
        assert cls.get_authors()
        assert cls.get_description()
        assert cls.get_icon()
    ```

    Una lista al principio del archivo es todo el registro que necesita un
    jugador nuevo en la batería de pruebas.

- **Fixtures.** Preparación reutilizable compartida entre pruebas (un documento de
  ejemplo, un archivo temporal), declarada una vez y solicitada por su nombre.
- **Ejecutar un subconjunto** mientras te centras en un área:

    ```bash
    pytest tests/test_game.py              # un archivo
    pytest -k timeout                      # pruebas cuyo nombre contiene "timeout"
    pytest -x                              # para en el primer fallo
    ```

!!! tip "Prueba el comportamiento, no la implementación"
    Afirma sobre lo que una función *devuelve o hace*, no sobre cómo lo hace. Así
    tus pruebas siguen pasando a través de refactorizaciones internas y solo fallan
    cuando el comportamiento realmente cambia — que es de lo que se trata.

## Probar un contrato que implementan otros

Cuando tu librería define una interfaz que rellenan personas de fuera (véase
[API § Diseñar una API que otros implementan](api.md#disenar-una-api-que-otros-implementan)),
las pruebas más valiosas son las que comprueban **todas** las implementaciones
contra las mismas reglas. `tests/test_players.py` hace jugar a cada jugador
admitido cinco tableros y afirma, en cada jugada, que la jugada devuelta era legal
y que no mutó el estado recibido.

Igual de valiosas: las pruebas que afirman que tu librería sobrevive a una
implementación que se porta mal. `tests/test_tournament.py` define stubs rotos a
propósito —`CrashBot`, `CheatBot`, `SlowBot`, `SlowBuildBot`, `GeneratorBot`,
`RenamerBot`— y afirma que cada uno pierde su propia partida mientras la
ejecución continúa. Esa es la diferencia entre un ejecutor que funciona y un
ejecutor que puedes dejar desatendido con el código de un desconocido dentro.

## Pruebas en integración continua

Ejecutar las pruebas en local está bien; ejecutarlas **automáticamente en cada
cambio** es lo que las convierte en una verdadera red de seguridad. El
[workflow `tests.yml`](../github/actions.md#ejecutar-las-pruebas) ejecuta `ruff`,
`mypy` y `pytest` en tres versiones de Python para cada push y pull request, de
modo que un cambio roto se señala en GitHub antes de que nadie lo fusione.

El paso final es hacer que esa comprobación sea **obligatoria**: con la
[protección de ramas](../github/repository-configuration.md#comprobaciones-de-estado-obligatorias),
un pull request no puede fusionarse mientras sus pruebas estén en rojo. El `pytest`
local, la CI y la protección de ramas forman entonces una cadena — detectas
problemas pronto, la CI detecta lo que se te escapó, y las reglas se aseguran de que
nada roto llegue a `main`.

## Adónde ir después

- [GitHub Actions](../github/actions.md) — el workflow que ejecuta estas pruebas.
- [Configuración del repositorio](../github/repository-configuration.md) — hacer
  de una suite en verde una condición para fusionar.
- [`tests/test_players.py`](https://github.com/jparisu/nim-arena/blob/main/tests/test_players.py)
  — la batería de contrato descrita arriba, completa.
