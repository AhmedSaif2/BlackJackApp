"""Console front-end, the Python counterpart of the original console project."""

from __future__ import annotations

import time
from typing import Callable

from .game import BET_OPTIONS, STARTING_POCKET_MONEY, Round
from .participants import Dealer, Player

DEALER_TURN_DELAY_SECONDS = 1.0


def _ask_bet(player: Player, ask: Callable[[str], str]) -> int:
    affordable = [bet for bet in BET_OPTIONS if player.can_afford(bet)]
    options = "/".join(str(bet) for bet in affordable)
    while True:
        answer = ask(f"Place a bet ({options}) or 'q' to quit: ").strip().lower()
        if answer == "q":
            return 0
        if answer.isdigit() and int(answer) in affordable:
            return int(answer)
        print("Please choose one of the listed bets.")


def _ask_hit(ask: Callable[[str], str]) -> bool:
    while True:
        answer = ask("Type 1 to Hit or 2 to Stand: ").strip()
        if answer in ("1", "2"):
            return answer == "1"


def play_round(player: Player, dealer: Dealer, bet: int, ask: Callable[[str], str], delay: float) -> None:
    game = Round(player, dealer, bet)
    print(" -------------------------- Player's turn --------------------------")
    print(f"Dealer shows: {dealer.hand}")
    while True:
        print(f"Your hand: {player.hand}")
        if not game.is_player_turn:
            break
        if _ask_hit(ask):
            game.hit()
        else:
            game.stand()

    if player.hand.is_twenty_one():
        print("Blackjack!")
    if not game.is_over:
        print(" -------------------------- Dealer's turn --------------------------")
        print(f"Dealer's hand: {dealer.hand}")
        while game.dealer_step() is not None:
            time.sleep(delay)
            print(f"Dealer's hand: {dealer.hand}")

    assert game.outcome is not None
    print(game.outcome.value)
    _print_stats(player)


def _print_stats(player: Player) -> None:
    for line in player.stats.summary_lines():
        print(line)


def main(ask: Callable[[str], str] = input, delay: float = DEALER_TURN_DELAY_SECONDS) -> None:
    print("-------------------------- New Game --------------------------")
    name = ""
    while not name:
        name = ask("Please Enter Your Name: ").strip()
    player = Player(name, STARTING_POCKET_MONEY)
    dealer = Dealer()

    while any(player.can_afford(bet) for bet in BET_OPTIONS):
        print(f"\nCurrent Pocket Money = {player.pocket_money}$")
        bet = _ask_bet(player, ask)
        if not bet:
            break
        play_round(player, dealer, bet, ask, delay)
    else:
        print("\nYou're out of money!")

    print(f"Thanks for playing, {player.name}! You leave with {player.pocket_money}$.")
    if player.stats.rounds_played:
        print("\n-------------------------- Scoreboard --------------------------")
        _print_stats(player)
