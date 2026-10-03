"""The people at the table: the player and the dealer."""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional

from .cards import Card, Deck
from .hand import Hand
from .stats import PlayerStats
from .jev import JevClient


class Action(Enum):
    HIT = "hit"
    STAND = "stand"


class Participant:
    def __init__(self, name: str) -> None:
        self.name = name
        self.hand = Hand()

    def add_card(self, card: Card) -> None:
        self.hand.add_card(card)

    def reset_hand(self) -> None:
        self.hand = Hand()


class Player(Participant):
    def __init__(self, name: str, pocket_money: int) -> None:
        super().__init__(name)
        self.pocket_money = pocket_money
        self.stats = PlayerStats(highest_pocket_money=pocket_money)

    def can_afford(self, amount: int) -> bool:
        return 0 < amount <= self.pocket_money

    def place_bet(self, amount: int) -> bool:
        """Take ``amount`` out of the pocket money. Returns False if it can't be afforded."""
        if not self.can_afford(amount):
            return False
        self.pocket_money -= amount
        return True

    def add_to_pocket_money(self, amount: int) -> None:
        self.pocket_money += amount


class Dealer(Participant):
    """The computer player. Jev decides each hit/stand; the fallback policy is used
    only when Jev isn't configured or doesn't answer."""

    # Fallback policy: always hit at or below this total, always stand at or above STAND_AT;
    # in between, it's a coin flip.
    ALWAYS_HIT_AT = 14
    STAND_AT = 19

    JEV_INSTRUCTIONS = (
        "You are the dealer in a game of blackjack, playing against one player. "
        "Decide whether to hit (draw another card) or stand, to maximise the chance of beating the player."
    )
    JEV_CRITERIA = {
        Action.HIT.value: "Draw another card",
        Action.STAND.value: "Keep the current hand and end the turn",
    }

    def __init__(self, rng: Optional[random.Random] = None, jev: Optional[JevClient] = None) -> None:
        super().__init__("The Dealer")
        self._rng = rng or random.Random()
        self.jev = jev if jev is not None else JevClient.from_env()

    def deal_card(self, deck: Deck, participant: Participant) -> Card:
        card = deck.draw()
        participant.add_card(card)
        return card

    def choose_action(self, opponent_total: Optional[int] = None) -> Action:
        answer = self.jev.ask_choice(self._describe_state(opponent_total), self.JEV_INSTRUCTIONS, self.JEV_CRITERIA)
        if answer is not None:
            return Action(answer)
        return self._fallback_action()

    def _describe_state(self, opponent_total: Optional[int]) -> str:
        lines = [
            "Rules: closest to 21 without going over wins; a tie is a draw. The player has already finished their turn.",
            f"Your cards: {', '.join(str(card) for card in self.hand.cards)}",
            f"Your total: {self.hand.total}" + (" (soft: an ace is counted as 11)" if self.hand.is_soft() else ""),
        ]
        if opponent_total is not None:
            lines.append(f"Player's final total: {opponent_total}")
        return "\n".join(lines)

    def _fallback_action(self) -> Action:
        total = self.hand.total
        if total <= self.ALWAYS_HIT_AT:
            return Action.HIT
        if total >= self.STAND_AT:
            return Action.STAND
        return self._rng.choice((Action.HIT, Action.STAND))
