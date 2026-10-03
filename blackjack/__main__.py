"""Entry point: ``python -m blackjack`` (GUI) or ``python -m blackjack --cli`` (console)."""

from __future__ import annotations

import argparse
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="blackjack", description="Play a game of Blackjack.")
    parser.add_argument("--cli", action="store_true", help="play in the terminal instead of the GUI")
    args = parser.parse_args(argv)

    try:
        if args.cli:
            from .cli import main as run
        else:
            from .gui import main as run
        run()
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
