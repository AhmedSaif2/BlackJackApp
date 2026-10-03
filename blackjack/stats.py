"""A player's running stats for the session, shown as a scoreboard by both front-ends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PlayerStats:
    rounds_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    # 21 on the first two cards.
    blackjacks: int = 0
    busts: int = 0
    # Money won minus money lost, across all rounds.
    net_winnings: int = 0
    highest_pocket_money: int = 0

    @property
    def win_rate(self) -> float:
        """Wins as a fraction of all rounds played (draws count as rounds); 0 before any round."""
        return self.wins / self.rounds_played if self.rounds_played else 0.0

    def record_win(self, bet: int) -> None:
        self.wins += 1
        self.net_winnings += bet
        self.rounds_played += 1

    def record_draw(self) -> None:
        self.draws += 1
        self.rounds_played += 1

    def record_loss(self, bet: int, bust: bool) -> None:
        self.losses += 1
        self.busts += bust
        self.net_winnings -= bet
        self.rounds_played += 1

    def record_blackjack(self) -> None:
        self.blackjacks += 1

    def update_pocket_money(self, pocket_money: int) -> None:
        self.highest_pocket_money = max(self.highest_pocket_money, pocket_money)

    def summary_lines(self) -> List[str]:
        return [
            f"Rounds: {self.rounds_played} | Wins: {self.wins} | Losses: {self.losses} | "
            f"Draws: {self.draws} | Win rate: {self.win_rate:.0%}",
            f"Blackjacks: {self.blackjacks} | Busts: {self.busts} | "
            f"Net: {self.net_winnings:+}$ | Best: {self.highest_pocket_money}$",
        ]
