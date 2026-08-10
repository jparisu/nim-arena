"""Make the repo root and ``web/`` importable for the test suite.

The ``players/`` directory is a namespace package (no ``__init__.py``); adding
the repo root to ``sys.path`` lets tests import individual bots for unit testing,
while the tournament/web load them via the manifest as usual. ``web/`` is added
so the browser bridge (``webglue.py``) can be tested like any other module.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
# `web/` is not a package and is not installed, but webglue.py is shipped code
# (it is what the browser calls into), so it needs to be importable to be tested.
sys.path.insert(0, str(_ROOT / "web"))
