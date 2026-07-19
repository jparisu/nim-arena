"""Player registry — the in-memory catalogue of available players.

The registry is a simple ``name -> Player`` dictionary. It is populated by
:mod:`nimarena.manifest`, which reads the human-edited ``players.yaml``. The
tournament and the web page both iterate over the registry; **neither ever
hard-codes player names**.

The registry is intentionally dumb: discovery (who gets admitted) lives in the
manifest so that the trust boundary is visible in a single PR diff.
"""

from __future__ import annotations

from .player import Player


class Registry:
    """A mapping of unique player name -> :class:`~nimarena.player.Player`."""

    def __init__(self) -> None:
        self._players: dict[str, Player] = {}

    def register(self, player: Player, *, replace: bool = False) -> None:
        """Add ``player`` to the registry.

        Args:
            player: an instance of a :class:`~nimarena.player.Player` subclass.
            replace: if ``False`` (default), registering a name that already
                exists raises. Set ``True`` to overwrite.

        Raises:
            TypeError: if ``player`` is not a :class:`Player`.
            ValueError: if the name is already taken and ``replace`` is False.
        """
        if not isinstance(player, Player):
            raise TypeError(f"{player!r} is not a Player instance")
        name = player.name
        if name in self._players and not replace:
            raise ValueError(f"A player named {name!r} is already registered")
        self._players[name] = player

    def get(self, name: str) -> Player:
        """Return the registered player named ``name`` (raises ``KeyError``)."""
        return self._players[name]

    def names(self) -> list[str]:
        """Return the registered player names, in insertion order."""
        return list(self._players)

    def all(self) -> list[Player]:
        """Return all registered player instances, in insertion order."""
        return list(self._players.values())

    def clear(self) -> None:
        """Remove every registered player."""
        self._players.clear()

    def __len__(self) -> int:
        return len(self._players)

    def __contains__(self, name: object) -> bool:
        return name in self._players


#: The default, process-wide registry used by the tournament and the web page.
REGISTRY = Registry()
