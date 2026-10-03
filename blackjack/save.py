"""Keeps your chips and stats between sessions, shared by the GUI and the console.

The save is a small JSON file in the user's config directory; set the
``BLACKJACK_SAVE_FILE`` environment variable to use a different file.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from .game import new_player
from .participants import Player
from .stats import PlayerStats

SAVE_FILE_ENV = "BLACKJACK_SAVE_FILE"


def default_save_path() -> Path:
    override = os.environ.get(SAVE_FILE_ENV)
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "BlackjackApp" / "save.json"


class SaveFile:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path is not None else default_save_path()

    def load(self) -> Player:
        """The saved player, or a fresh one if there's no save or it can't be read."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            pocket_money = int(data["pocket_money"])
            stats = PlayerStats.from_dict(data.get("stats", {}))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return new_player()
        if pocket_money < 0:
            return new_player()
        player = new_player()
        player.pocket_money = pocket_money
        player.stats = stats
        stats.update_pocket_money(pocket_money)
        return player

    def save(self, player: Player) -> None:
        """Write the save; failures are ignored so a read-only disk never stops the game."""
        data = {"pocket_money": player.pocket_money, "stats": player.stats.to_dict()}
        temp = self.path.with_suffix(".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
        except OSError:
            pass
