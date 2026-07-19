"""Manifest-based player discovery.

Players are discovered from an **explicit, human-edited manifest**
(``players.yaml``) — never by auto-scanning a folder. This is a deliberate
design choice: when someone opens a PR to add a bot, the reviewer sees, in a
single diff, both the new file and the one line that admits it. That legibility
*is* the security gate; auto-importing a directory would hide what is being
admitted and would run a stranger's top-level code merely to discover it.

Manifest format (``players.yaml`` at the repo root)::

    players:
      - name: RandomBot          # unique, human-readable; must match Player.name
        author: NIM Arena Team   # who wrote it (shown for credit)
        file: random_bot.py      # path to the .py file (see resolution below)
        class: RandomBot         # the Player subclass to instantiate

Path resolution for ``file``:

* A bare filename (e.g. ``random_bot.py``) is resolved inside the ``players/``
  directory.
* A path with a separator (e.g. ``community/foo/bar.py``) is resolved relative
  to the repo root.

Loading a player *imports its file*, which runs that file's top-level code. That
is expected and safe **only because** files arrive through reviewed PRs.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .player import Player
from .registry import REGISTRY, Registry

#: Repo root, inferred as the parent of ``src/``.
REPO_ROOT = Path(__file__).resolve().parents[2]
#: Default manifest location.
DEFAULT_MANIFEST = REPO_ROOT / "players.yaml"
#: Default directory holding community player files.
DEFAULT_PLAYERS_DIR = REPO_ROOT / "players"


@dataclass
class ManifestEntry:
    """One line of the manifest, already parsed and validated."""

    name: str
    author: str
    file: str
    cls: str


class ManifestError(Exception):
    """Raised when the manifest itself is malformed (not when a bot misbehaves)."""


def parse_manifest(manifest_path: str | Path) -> list[ManifestEntry]:
    """Parse ``players.yaml`` into a list of :class:`ManifestEntry`.

    Raises:
        ManifestError: if the file is missing, unparseable, or an entry is
            missing a required field.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise ManifestError(f"Manifest not found: {path}")
    try:
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise ManifestError(f"Could not parse {path}: {exc}") from exc

    if not isinstance(data, dict) or "players" not in data:
        raise ManifestError("Manifest must be a mapping with a top-level 'players' list")
    raw_players = data["players"]
    if not isinstance(raw_players, list):
        raise ManifestError("'players' must be a list")

    entries: list[ManifestEntry] = []
    for i, raw in enumerate(raw_players):
        if not isinstance(raw, dict):
            raise ManifestError(f"players[{i}] must be a mapping")
        try:
            entries.append(
                ManifestEntry(
                    name=str(raw["name"]),
                    author=str(raw.get("author", "unknown")),
                    file=str(raw["file"]),
                    cls=str(raw["class"]),
                )
            )
        except KeyError as exc:
            raise ManifestError(f"players[{i}] is missing required field {exc}") from exc
    return entries


def _resolve_file(file: str, players_dir: Path, repo_root: Path) -> Path:
    """Resolve a manifest ``file`` field to an absolute path (see module docs)."""
    p = Path(file)
    if p.is_absolute():
        return p
    if len(p.parts) == 1:  # bare filename -> players/
        return players_dir / p
    return repo_root / p


def _load_class_from_file(path: Path, class_name: str) -> type[Player]:
    """Import ``path`` and return its ``class_name`` attribute.

    The module is loaded under a unique synthetic name so that two player files
    that happen to share a filename never collide in ``sys.modules``.
    """
    if not path.exists():
        raise ManifestError(f"Player file not found: {path}")
    module_name = f"nimarena_player_{path.stem}_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ManifestError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    try:
        obj = getattr(module, class_name)
    except AttributeError as exc:
        raise ManifestError(f"{path} has no class {class_name!r}") from exc
    if not (isinstance(obj, type) and issubclass(obj, Player)):
        raise ManifestError(f"{class_name!r} in {path} is not a Player subclass")
    return obj


def load_players(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    players_dir: str | Path = DEFAULT_PLAYERS_DIR,
    registry: Registry | None = None,
    *,
    strict: bool = False,
) -> Registry:
    """Load every player named in the manifest into a registry.

    Args:
        manifest_path: path to ``players.yaml``.
        players_dir: directory used to resolve bare filenames.
        registry: registry to populate; defaults to the global
            :data:`~nimarena.registry.REGISTRY` (cleared first).
        strict: if ``True``, any bad entry raises. If ``False`` (default), a bad
            entry is skipped with a warning printed to stderr so that one broken
            submission never blocks loading the rest.

    Returns:
        The populated registry.
    """
    if registry is None:
        registry = REGISTRY
        registry.clear()

    repo_root = Path(manifest_path).resolve().parent
    players_dir = Path(players_dir)
    entries = parse_manifest(manifest_path)

    for entry in entries:
        try:
            path = _resolve_file(entry.file, players_dir, repo_root)
            cls = _load_class_from_file(path, entry.cls)
            instance = cls()
            if instance.name != entry.name:
                # Keep the manifest name authoritative and visible.
                instance.name = entry.name
            registry.register(instance, replace=True)
        except Exception as exc:  # noqa: BLE001 - one bad bot must not stop the rest
            if strict:
                raise
            print(f"[manifest] skipping {entry.name!r}: {exc}", file=sys.stderr)
    return registry
