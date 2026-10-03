"""Playing cards and the deck they are dealt from."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Iterator, Optional


class Suit(Enum):
    HEART = "heart"
    DIAMOND = "diamond"
    CLUB = "club"
    SPADE = "spade"


RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace")
FACE_RANKS = ("jack", "queen", "king")


@dataclass(frozen=True)
class Card:
    rank: str
    suit: Suit

    def __post_init__(self) -> None:
        if self.rank not in RANKS:
            raise ValueError(f"Invalid card rank: {self.rank!r}")

    @property
    def value(self) -> int:
        """Blackjack value of the card. Aces count as 11 here; Hand softens them."""
        if self.rank == "ace":
            return 11
        if self.rank in FACE_RANKS:
            return 10
        return int(self.rank)

    @property
    def is_ace(self) -> bool:
        return self.rank == "ace"

    @property
    def image_name(self) -> str:
        """File name (without extension) of this card's image, e.g. ``ace_of_spades``."""
        return f"{self.rank}_of_{self.suit.value}s"

    def __str__(self) -> str:
        return f"{self.rank.capitalize()} of {self.suit.value.capitalize()}s"


class Deck:
    """A deck of cards. Cards are drawn from the top (end of the list)."""

    def __init__(self, cards: Optional[Iterable[Card]] = None, rng: Optional[random.Random] = None):
        if cards is None:
            cards = (Card(rank, suit) for rank in RANKS for suit in Suit)
        self._cards = list(cards)
        self._rng = rng or random.Random()

    def shuffle(self) -> None:
        self._rng.shuffle(self._cards)

    def draw(self) -> Card:
        if not self._cards:
            raise IndexError("Cannot draw from an empty deck")
        return self._cards.pop()

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)
