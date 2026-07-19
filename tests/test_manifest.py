"""Tests for the manifest loader and registry."""

from __future__ import annotations

import textwrap

import pytest

from nimarena.manifest import ManifestError, load_players, parse_manifest
from nimarena.player import Player
from nimarena.registry import Registry


def test_parse_real_manifest_has_reference_players():
    from nimarena.manifest import DEFAULT_MANIFEST

    entries = parse_manifest(DEFAULT_MANIFEST)
    names = {e.name for e in entries}
    assert {"RandomBot", "MinimaxBot", "PerfectBot"} <= names


def test_missing_manifest_raises(tmp_path):
    with pytest.raises(ManifestError):
        parse_manifest(tmp_path / "does_not_exist.yaml")


def test_malformed_manifest_raises(tmp_path):
    bad = tmp_path / "players.yaml"
    bad.write_text("players:\n  - name: X\n")  # missing 'file' and 'class'
    with pytest.raises(ManifestError):
        parse_manifest(bad)


def test_load_from_custom_dir(tmp_path):
    players_dir = tmp_path / "players"
    players_dir.mkdir()
    (players_dir / "tiny.py").write_text(
        textwrap.dedent(
            """
            from nimarena.player import Player
            class Tiny(Player):
                name = "Tiny"
                def choose_move(self, state):
                    for i, s in enumerate(state):
                        if s: return (i, 1)
            """
        )
    )
    manifest = tmp_path / "players.yaml"
    manifest.write_text(
        "players:\n  - name: Tiny\n    author: me\n    file: tiny.py\n    class: Tiny\n"
    )
    reg = load_players(manifest, players_dir, Registry(), strict=True)
    assert reg.names() == ["Tiny"]
    assert isinstance(reg.get("Tiny"), Player)


def test_bad_entry_skipped_when_not_strict(tmp_path, capsys):
    manifest = tmp_path / "players.yaml"
    manifest.write_text(
        "players:\n  - name: Ghost\n    author: me\n    file: missing.py\n    class: Ghost\n"
    )
    reg = load_players(manifest, tmp_path, Registry(), strict=False)
    assert reg.names() == []  # bad entry skipped, no crash
    assert "skipping" in capsys.readouterr().err


def test_registry_rejects_duplicate_names():
    from players.random_bot import RandomBot

    reg = Registry()
    reg.register(RandomBot())
    with pytest.raises(ValueError):
        reg.register(RandomBot())
    reg.register(RandomBot(), replace=True)  # ok with replace
    assert len(reg) == 1
