"""A single round of blackjack, shared by the GUI and the console front-ends."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from .cards import Card, Deck
from .participants import Action, Dealer, Participant, Player

STARTING_POCKET_MONEY = 2500
BET_OPTIONS = (10, 50, 200)


class Outcome(Enum):
    WIN = "You Won!"
    DRAW = "Draw!"
    LOSE = "You Lost!"


class Round:
    """One hand of blackjack.

    The bet is taken from the player up front. The player is dealt two cards and the
    dealer one; the player then hits or stands, after which the dealer plays one step
    at a time (so a UI can reveal the dealer's cards gradually). When the round ends,
    winnings are paid out (double the bet on a win, the bet back on a draw) and the
    result is recorded in the player's stats.
    """

    def __init__(self, player: Player, dealer: Dealer, bet: int, deck: Optional[Deck] = None):
        if not player.place_bet(bet):
            raise ValueError(f"{player.name} cannot afford a bet of {bet}")
        self.player = player
        self.dealer = dealer
        self.bet = bet
        self.outcome: Optional[Outcome] = None
        self._player_standing = False

        if deck is None:
            deck = Deck()
            deck.shuffle()
        self.deck = deck

        player.reset_hand()
        dealer.reset_hand()
        self._deal(player)
        self._deal(player)
        self._deal(dealer)
        self.is_blackjack = player.hand.is_twenty_one()
        self._stand_on_twenty_one()

    @property
    def is_player_turn(self) -> bool:
        return self.outcome is None and not self._player_standing

    @property
    def is_over(self) -> bool:
        return self.outcome is not None

    def hit(self) -> Card:
        if not self.is_player_turn:
            raise RuntimeError("It is not the player's turn")
        card = self._deal(self.player)
        if self.player.hand.is_bust():
            self._finish(Outcome.LOSE)
        else:
            self._stand_on_twenty_one()
        return card

    def stand(self) -> None:
        if not self.is_player_turn:
            raise RuntimeError("It is not the player's turn")
        self._player_standing = True

    def dealer_step(self) -> Optional[Card]:
        """Make one dealer decision.

        Returns the card the dealer drew, or None once the dealer is done, at which
        point the round has been settled and ``outcome`` is set.
        """
        if self.is_player_turn:
            raise RuntimeError("The player has not finished their turn")
        if self.is_over:
            return None
        hand = self.dealer.hand
        if hand.is_twenty_one() or hand.is_bust() or self.dealer.choose_action(self.player.hand.total) is Action.STAND:
            self._settle()
            return None
        return self._deal(self.dealer)

    def play_dealer(self) -> List[Card]:
        """Run the dealer's whole turn at once. Returns the cards drawn."""
        drawn = []
        while (card := self.dealer_step()) is not None:
            drawn.append(card)
        return drawn

    def _deal(self, participant: Participant) -> Card:
        return self.dealer.deal_card(self.deck, participant)

    def _stand_on_twenty_one(self) -> None:
        if self.player.hand.is_twenty_one():
            self._player_standing = True

    def _settle(self) -> None:
        player_total = self.player.hand.total
        dealer_total = self.dealer.hand.total
        if self.dealer.hand.is_bust() or player_total > dealer_total:
            self._finish(Outcome.WIN)
        elif player_total == dealer_total:
            self._finish(Outcome.DRAW)
        else:
            self._finish(Outcome.LOSE)

    def _finish(self, outcome: Outcome) -> None:
        self.outcome = outcome
        stats = self.player.stats
        if outcome is Outcome.WIN:
            self.player.add_to_pocket_money(self.bet * 2)
            stats.record_win(self.bet)
        elif outcome is Outcome.DRAW:
            self.player.add_to_pocket_money(self.bet)
            stats.record_draw()
        else:
            stats.record_loss(self.bet, bust=self.player.hand.is_bust())
        if self.is_blackjack:
            stats.record_blackjack()
        stats.update_pocket_money(self.player.pocket_money)
