"""Console front-end, the Python counterpart of the original console project."""

from __future__ import annotations

import time
from typing import Callable, Optional, Union

from .game import BET_OPTIONS, Round, new_player
from .participants import Dealer, Player
from .save import SaveFile

DEALER_TURN_DELAY_SECONDS = 1.0

QUIT = "q"
NEW_GAME = "n"


def _ask_bet(player: Player, last_bet: Optional[int], ask: Callable[[str], str]) -> Union[int, str]:
    """A bet, or QUIT / NEW_GAME. Pressing Enter repeats the last bet if it's still affordable."""
    affordable = [bet for bet in BET_OPTIONS if player.can_afford(bet)]
    repeat = last_bet if last_bet in affordable else None
    options = "/".join(str(bet) for bet in affordable)
    prompt = f"Bet {options}" + (f", Enter for {repeat} again" if repeat else "") + ", 'n' new game, 'q' quit: "
    while True:
        answer = ask(prompt).strip().lower()
        if answer in (QUIT, NEW_GAME):
            return answer
        if not answer and repeat:
            return repeat
        if answer.isdigit() and int(answer) in affordable:
            return int(answer)
        print("Please choose one of the listed bets.")


def _ask_start_over(ask: Callable[[str], str]) -> bool:
    while True:
        answer = ask("You're out of chips! Type 'n' to start over or 'q' to quit: ").strip().lower()
        if answer in (QUIT, NEW_GAME):
            return answer == NEW_GAME


def _ask_hit(ask: Callable[[str], str]) -> bool:
    while True:
        answer = ask("Hit or stand? (h/s): ").strip().lower()
        if answer in ("h", "s", "1", "2"):
            return answer in ("h", "1")


def play_round(player: Player, dealer: Dealer, bet: int, ask: Callable[[str], str], delay: float, save: SaveFile) -> None:
    game = Round(player, dealer, bet)
    # Save once the bet is down, so quitting mid-hand doesn't undo a losing hand.
    save.save(player)
    print(" -------------------------- Your turn --------------------------")
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
        print("Blackjack!" if game.is_blackjack else "21!")
    if not game.is_over:
        print(" -------------------------- Dealer's turn --------------------------")
        print(f"Dealer's hand: {dealer.hand}")
        while game.dealer_step() is not None:
            time.sleep(delay)
            print(f"Dealer's hand: {dealer.hand}")

    assert game.outcome is not None
    print(game.outcome.value)
    save.save(player)
    _print_stats(player)


def _print_stats(player: Player) -> None:
    for line in player.stats.summary_lines():
        print(line)


def main(
    ask: Callable[[str], str] = input, delay: float = DEALER_TURN_DELAY_SECONDS, save: Optional[SaveFile] = None
) -> None:
    save = save if save is not None else SaveFile()
    player = save.load()
    dealer = Dealer()
    last_bet: Optional[int] = None

    print("-------------------------- Blackjack --------------------------")
    if player.stats.rounds_played:
        print("Welcome back! Your chips and stats were saved from last time.")

    while True:
        print(f"\nChips: {player.pocket_money}$")
        if not any(player.can_afford(bet) for bet in BET_OPTIONS):
            choice: Union[int, str] = NEW_GAME if _ask_start_over(ask) else QUIT
        else:
            choice = _ask_bet(player, last_bet, ask)
        if choice == QUIT:
            break
        if choice == NEW_GAME:
            player, last_bet = new_player(), None
            save.save(player)
            print("New game! Your chips and stats have been reset.")
            continue
        assert isinstance(choice, int)
        last_bet = choice
        play_round(player, dealer, choice, ask, delay, save)

    print(f"Thanks for playing! You leave with {player.pocket_money}$. Your progress is saved.")
    if player.stats.rounds_played:
        print("\n-------------------------- Scoreboard --------------------------")
        _print_stats(player)
