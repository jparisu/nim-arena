# Primeros pasos

## Instalar la librería

Requiere Python 3.10 o superior.

```bash
git clone https://github.com/jparisu/nim-arena
cd nim-arena
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

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

## Ejecutar las pruebas

```bash
pytest
```

La batería comprueba las reglas del juego, que cada jugador de referencia devuelve
jugadas legales y no muta el estado, que las IA de referencia se ordenan como se
espera, y que el torneo sobrevive a bots que se cuelgan, se rompen o hacen
trampas.

## Ejecutar el torneo en local

```bash
# Torneo "simple" por defecto sobre los tableros por defecto -> results/leaderboard.json
nim-tournament --out results/leaderboard.json

# Elige formato: simple (por defecto), league (Elo) o championship (cuadro):
nim-tournament --tournament championship

# Más rápido, en un solo proceso (tiempo blando — no puede matar un bot colgado):
nim-tournament --no-subprocess

# Presupuesto por jugador, en segundos (para una partida entera Y para construir):
nim-tournament --time-limit 2.0

# Tableros propios (repite la opción):
nim-tournament --board 3,5,7 --board 7,9,11
```

Consulta [El torneo](advanced/tournament.md) para saber cómo funcionan los tiempos y las
descalificaciones, y [El marcador](advanced/scoreboard.md) para el contenido del archivo de
resultados.

## Ejecutar la página web en local

La página carga el Python compartido mediante Pyodide. Primero ensambla el
paquete, luego sirve la carpeta `web/` con cualquier servidor estático:

```bash
python scripts/build_web.py           # -> web/py.zip y web/leaderboard.json
python -m http.server -d web 8000     # abre http://localhost:8000
```

!!! note
    Pyodide se descarga de un CDN la primera vez que se carga la página, así que
    el navegador necesita acceso a internet. Todo lo demás se ejecuta localmente
    en tu navegador.

## Adónde ir después

- [Reglas del juego](rules.md) — contra qué estás programando en realidad.
- [API de jugador](upload-a-bot/player-api.md) — la interfaz que implementa toda IA.
- [Enviar un jugador](upload-a-bot/submit-a-player.md) — mete el tuyo en el torneo.
- [Guía → MkDocs](../guide/documentation/mkdocs.md) — construir
  este sitio de documentación en local, y cómo está montado.
