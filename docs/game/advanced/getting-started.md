# Primeros pasos

Cuatro cosas que puedes hacer con el proyecto en local, de menos a más.

| Quiero… | Comando |
|---|---|
| 🔧 instalarlo | `pip install -e ".[dev]"` |
| 🎮 jugar una partida | desde Python, [abajo](#jugar-una-partida-desde-python) |
| ✅ ejecutar las pruebas | `pytest` |
| 🏆 ejecutar un torneo | `nim-tournament` |

!!! tip "¿Solo quieres jugar?"
    No hace falta instalar nada: la
    [página web](https://jparisu.github.io/nim-arena) ejecuta el mismo Python en
    tu navegador.

---

## Instalar la librería

Requiere Python 3.10 o superior.

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Jugar una partida desde Python

```python
from nimarena import game
from nimarena.manifest import load_players

registry = load_players()          # lee los dos manifiestos players.yaml
hard = registry.get("hard")
random_bot = registry.get("random")

state = [3, 5, 7]
turn = 0
players = [hard, random_bot]
while not game.is_terminal(state):
    move = players[turn].choose_move(state)
    print(f"{players[turn].name} plays {move} on {state}")
    state = game.apply_move(state, move)
    turn = 1 - turn
print("Winner:", players[1 - turn].name)
```

---

## Ejecutar las pruebas

```bash
pytest
```

La batería comprueba las reglas del juego, que cada jugador de referencia
devuelve jugadas legales y no muta el estado, que las IA de referencia se
ordenan como se espera, y que el torneo sobrevive a bots que se cuelgan, se
rompen o hacen trampas.

---

## Ejecutar el torneo en local

```bash
# Escribe la clasificación en results/leaderboard.json
nim-tournament --out results/leaderboard.json

# Más rápido para probar tu bot mientras lo escribes
nim-tournament --no-subprocess

# Tableros propios (repite la opción)
nim-tournament --board 3,5,7 --board 7,9,11
```

Consulta [El torneo](tournament.md) para los formatos, los tiempos y
las descalificaciones.

---

## Ejecutar la página web en local

La página carga el Python compartido mediante Pyodide. Primero ensambla el
paquete, luego sirve la carpeta `web/` con cualquier servidor estático:

```bash
python scripts/build_web.py           # -> web/py.zip y web/leaderboard.json
python -m http.server -d web 8000     # abre http://localhost:8000
```

!!! warning "Sírvela, no la abras con doble clic"
    Con `file://` el navegador bloquea `fetch()` y la página no carga. Usa
    siempre un servidor, aunque sea el de una línea de arriba.

!!! note "La primera carga necesita internet"
    Pyodide se descarga de un CDN la primera vez. Todo lo demás se ejecuta
    localmente en tu navegador.

---

**Siguiente:** [API de jugador](../upload-a-bot/player-api.md) — escribe tu primera
IA en veinte líneas.
