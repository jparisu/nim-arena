"""Make the repo root importable so tests can ``import players.<bot>`` directly.

The ``players/`` directory is a namespace package (no ``__init__.py``); adding
the repo root to ``sys.path`` lets tests import individual bots for unit testing,
while the tournament/web load them via the manifest as usual.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
