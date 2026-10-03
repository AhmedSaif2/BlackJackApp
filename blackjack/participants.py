"""The people at the table: the player and the dealer."""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional

from .cards import Card, Deck
from .hand import Hand
from .stats import PlayerStats


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
    # Always hit at or below this total, always stand at or above STAND_AT; in between, it's a coin flip.
    ALWAYS_HIT_AT = 14
    STAND_AT = 19

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        super().__init__("The Dealer")
        self._rng = rng or random.Random()

    def deal_card(self, deck: Deck, participant: Participant) -> Card:
        card = deck.draw()
        participant.add_card(card)
        return card

    def choose_action(self) -> Action:
        total = self.hand.total
        if total <= self.ALWAYS_HIT_AT:
            return Action.HIT
        if total >= self.STAND_AT:
            return Action.STAND
        return self._rng.choice((Action.HIT, Action.STAND))
