# Enviar un jugador nuevo por pull request

Los jugadores nuevos llegan por **pull request**. No hay ningún formulario de
subida aparte: haces un fork del repositorio, añades un archivo, añades una línea
al manifiesto y abres un PR. Alguien lo revisa y lo fusiona. Tu código solo se
ejecuta *después* de que una persona acepte el PR — que es exactamente por lo que
la revisión es la puerta de seguridad.

## Paso 1 — Fork y rama

Haz un fork de [`jparisu/nim-arena`](https://github.com/jparisu/nim-arena), clona
tu fork y crea una rama:

```bash
git clone https://github.com/<tu-usuario>/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
git checkout -b add-my-bot
```

## Paso 2 — Añade el archivo de tu jugador

Crea `players/<tu_bot>.py`. Lo más fácil es empezar copiando
[`players/builtin/random.py`](player-api.md). Tu clase debe:

- heredar de `nimarena.player.Player`,
- implementar `get_name`, `get_authors`, `get_description` y `get_icon` — el
  nombre debe ser **único** entre todos los jugadores admitidos, y el icono es un
  solo emoji,
- implementar `choose_move(self, state) -> (fila, cantidad)` devolviendo una
  jugada **legal**.

```python
# players/custom/corner_bot.py
from nimarena.game import State, legal_moves, nim_sum
from nimarena.player import Player


class CornerBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "corner"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["tu-usuario-de-github"]

    @classmethod
    def get_description(cls) -> str:
        return "Reduces a row to leave a zero nim-sum whenever one exists."

    @classmethod
    def get_icon(cls) -> str:
        return "📐"

    def choose_move(self, state: State) -> tuple[int, int]:
        # Intenta dejar el nim-sum a cero; si no, retira un solo palo.
        target = nim_sum(state)
        for row, sticks in enumerate(state):
            reduce_to = sticks ^ target
            if reduce_to < sticks:
                return (row, sticks - reduce_to)
        return legal_moves(state)[0]
```

## Paso 3 — Regístralo en el manifiesto

Añade **exactamente una entrada** a
[`players/custom/players.yaml`](https://github.com/jparisu/nim-arena/blob/main/players/custom/players.yaml):

```yaml
  - file: corner_bot.py
    class: CornerBot
```

El manifiesto es solo una lista de admisión: qué archivo y qué clase. Tu nombre,
autores y descripción vienen de la propia clase, así que aquí no hay nada que
mantener sincronizado con tu código.

Hay exactamente **dos** campos que escribir:

| Campo | Significado |
|-------|-------------|
| `file` | el archivo `.py`. Un nombre suelto se resuelve junto al manifiesto, en `players/custom/`; una ruta con `/` se resuelve desde la raíz del repositorio. |
| `class` | la subclase de `Player` que se admite |

!!! info "¿Por qué un manifiesto y no un escaneo de la carpeta?"
    El manifiesto hace **visible** la frontera de confianza. En un solo diff de PR
    quien revisa ve tanto tu archivo nuevo como la única línea que lo admite. Un
    escaneo automático ocultaría qué se está admitiendo y ejecutaría tu código de
    nivel superior solo para descubrirlo.

## Paso 4 — Verifica en local

```bash
pytest                         # debe estar verde
nim-tournament --no-subprocess # juega tu bot contra los jugadores de referencia
```

!!! tip "Ejecuta el torneo, no solo los tests"
    El torneo es lo que juega con tu bot, así que es lo que detecta una jugada
    ilegal, un fallo o un tiempo agotado — y un bot que haga cualquiera de esas
    cosas no se fusiona. Hazlo antes de abrir el PR.

## Paso 5 — Abre el pull request

Sube tu rama y abre un PR desde tu fork. El repositorio incluye una plantilla
específica para jugadores nuevos en
[`.github/PULL_REQUEST_TEMPLATE/new_player.md`](https://github.com/jparisu/nim-arena/blob/main/.github/PULL_REQUEST_TEMPLATE/new_player.md);
selecciónala añadiendo `?template=new_player.md` a la URL del PR, o pégala tú en
la descripción. Es la misma lista contra la que revisa quien mantiene el
repositorio, así que rellenarla con honestidad es la vía más rápida a la fusión.

CI se ejecuta en cada push al PR: `ruff`, `mypy`, `pytest` en tres versiones de
Python, un torneo de humo y una construcción estricta de la documentación. Una
comprobación en rojo es una fusión bloqueada.

Si todo esto te resulta nuevo, la [guía del estudiante](../guide/index.md) cubre
[forks y ramas](../guide/github/workflow.md),
[pull requests](../guide/github/pull-requests.md) y
[qué hacen las comprobaciones de CI](../guide/github/actions.md).

## Criterios de aceptación (la lista de quien revisa)

Tu PR se fusiona solo si pasa **todos** estos puntos. Son la puerta explícita y
documentada del proyecto:

1. **Diseño** — un archivo en `players/custom/`, una línea de manifiesto, hereda de
   `Player`, `name` único, mínimo y legible.
2. **Corrección** — CI en verde; el bot devuelve jugadas legales y nunca muta el
   estado; no falla ni agota el tiempo frente a los bots de referencia.
3. **Sin malware** — quien revisa lee el código. Nada de red, sistema de archivos,
   subprocesos, `eval`/`exec`, ofuscación ni intentos de leer secretos o escapar
   del entorno. Cualquier cosa sospechosa se rechaza a la vista.

!!! danger "Un jugador que falla o agota el tiempo no se fusiona"
    La robustez de tu bot es **tu** responsabilidad. El torneo sobrevivirá a un
    jugador malo (pierde la partida y la ejecución continúa), pero no lo
    publicamos.

## Resumen de reglas

- Devuelve una jugada legal `(fila, cantidad)`.
- No mutes `state`.
- Declara un nombre único; CI rechaza un nombre que ya use un jugador admitido.
- Sin dependencias externas más allá de la librería estándar y `nimarena`.
- Sin acceso a red, sistema de archivos ni subprocesos — sé una función pura del
  tablero.
- Sé rápido: el torneo impone un presupuesto por jugador para una partida entera,
  más otro aparte para la construcción, y ambos se **miden en los runners de
  GitHub**, más lentos y variables que tu portátil. Un bot que pasa en local
  todavía puede agotar el tiempo en la ejecución evaluada — elige código
  eficiente.

## Adónde ir después

- [API de jugador](player-api.md) — el contrato completo, y lo que el torneo exige
  además.
- [Pull requests](../guide/github/pull-requests.md) — cómo abrir uno y cómo se
  revisa.
