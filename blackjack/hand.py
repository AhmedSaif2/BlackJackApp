"""A participant's hand, with flexible ace handling."""

from __future__ import annotations

from typing import List

from .cards import Card


class Hand:
    def __init__(self) -> None:
        self.cards: List[Card] = []
        self._total = 0
        # Aces currently counted as 11 that can still drop to 1.
        self._soft_aces = 0

    def add_card(self, card: Card) -> None:
        self.cards.append(card)
        self._total += card.value
        if card.is_ace:
            self._soft_aces += 1
        # Count aces as 1 instead of 11 for as long as that keeps the hand from busting.
        while self._total > 21 and self._soft_aces:
            self._total -= 10
            self._soft_aces -= 1

    @property
    def total(self) -> int:
        return self._total

    def is_soft(self) -> bool:
        """True while an ace is being counted as 11."""
        return self._soft_aces > 0

    def is_twenty_one(self) -> bool:
        return self._total == 21

    def is_bust(self) -> bool:
        return self._total > 21

    def __len__(self) -> int:
        return len(self.cards)

    def __str__(self) -> str:
        return ", ".join(str(card) for card in self.cards) + f" (total {self._total})"
