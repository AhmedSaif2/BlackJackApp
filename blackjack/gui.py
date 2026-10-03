"""Tkinter front-end: welcome page -> betting page -> game page."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Dict, Optional

from .cards import Card
from .game import BET_OPTIONS, STARTING_POCKET_MONEY, Outcome, Round
from .participants import Dealer, Participant, Player

CARD_IMAGES_DIR = Path(__file__).parent / "assets" / "playing_cards"
# The source images are 500x726; shrinking by 7 gives roughly 72x104 cards on screen.
CARD_IMAGE_SUBSAMPLE = 7
DEALER_TURN_DELAY_MS = 1000

TABLE_GREEN = "#2e8b57"  # SeaGreen, as in the original WinForms app
TEXT_COLOR = "white"
TITLE_FONT = ("Segoe UI", 36)
LABEL_FONT = ("Segoe UI", 20)
BUTTON_FONT = ("Segoe UI", 15)
SCOREBOARD_FONT = ("Segoe UI", 12)


class CardImages:
    """Loads card images on first use and keeps references so Tk doesn't drop them."""

    def __init__(self) -> None:
        self._cache: Dict[str, tk.PhotoImage] = {}

    def get(self, card: Card) -> tk.PhotoImage:
        name = card.image_name
        if name not in self._cache:
            image = tk.PhotoImage(file=str(CARD_IMAGES_DIR / f"{name}.png"))
            self._cache[name] = image.subsample(CARD_IMAGE_SUBSAMPLE)
        return self._cache[name]


def _label(parent: tk.Misc, text: str = "", font=LABEL_FONT) -> tk.Label:
    return tk.Label(parent, text=text, font=font, bg=TABLE_GREEN, fg=TEXT_COLOR)


def _button(parent: tk.Misc, text: str, command: Callable[[], None]) -> tk.Button:
    return tk.Button(parent, text=text, font=BUTTON_FONT, width=8, bg="white", command=command)


class WelcomePage(tk.Frame):
    def __init__(self, master: tk.Misc, on_play: Callable[[Player], None]):
        super().__init__(master, bg=TABLE_GREEN)
        self._on_play = on_play

        _label(self, "Blackjack", TITLE_FONT).pack(pady=(90, 50))
        row = tk.Frame(self, bg=TABLE_GREEN)
        row.pack()
        _label(row, "Enter Your Name").pack(side=tk.LEFT, padx=(0, 20))
        self._name = tk.Entry(row, font=LABEL_FONT, width=16)
        self._name.pack(side=tk.LEFT)
        self._name.bind("<Return>", lambda _event: self._play())
        self._name.focus_set()
        _button(self, "Play", self._play).pack(pady=50)

    def _play(self) -> None:
        name = self._name.get().strip()
        if not name:
            messagebox.showinfo("Blackjack", "Please enter your name!")
            return
        self._on_play(Player(name, STARTING_POCKET_MONEY))


class BettingPage(tk.Frame):
    def __init__(self, master: tk.Misc, player: Player, on_bet: Callable[[int], None], on_restart: Callable[[], None]):
        super().__init__(master, bg=TABLE_GREEN)

        _label(self, f"Welcome {player.name}").pack(pady=(90, 30))
        _label(self, f"Pocket Money = {player.pocket_money}$").pack()
        if player.stats.rounds_played:
            self._scoreboard(player).pack(side=tk.BOTTOM, pady=(0, 30))

        if not any(player.can_afford(bet) for bet in BET_OPTIONS):
            _label(self, "You're out of money!").pack(pady=(50, 30))
            _button(self, "Start over", on_restart).pack()
            return

        _label(self, "Place your bet").pack(pady=(50, 30))
        row = tk.Frame(self, bg=TABLE_GREEN)
        row.pack()
        for bet in BET_OPTIONS:
            button = _button(row, f"{bet}$", lambda bet=bet: on_bet(bet))
            if not player.can_afford(bet):
                button.config(state=tk.DISABLED)
            button.pack(side=tk.LEFT, padx=50)

    def _scoreboard(self, player: Player) -> tk.Frame:
        board = tk.Frame(self, bg=TABLE_GREEN)
        _label(board, "Scoreboard", BUTTON_FONT).pack()
        for line in player.stats.summary_lines():
            _label(board, line, SCOREBOARD_FONT).pack()
        return board


class GamePage(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        player: Player,
        bet: int,
        card_images: CardImages,
        on_round_over: Callable[[Player], None],
    ):
        super().__init__(master, bg=TABLE_GREEN)
        self._player = player
        self._card_images = card_images
        self._on_round_over = on_round_over

        self._dealer_cards, self._dealer_sum = self._hand_area("Dealer Cards")
        self._player_cards, self._player_sum = self._hand_area("Your Cards")

        controls = tk.Frame(self, bg=TABLE_GREEN)
        controls.pack(fill=tk.X, padx=65, pady=20)
        self._hit_button = _button(controls, "Hit", self._hit)
        self._hit_button.pack(side=tk.LEFT, padx=(25, 40))
        self._stand_button = _button(controls, "Stand", self._stand)
        self._stand_button.pack(side=tk.LEFT)
        _label(controls, f"Bet = {bet}$").pack(side=tk.RIGHT)

        self._round = Round(player, Dealer(), bet)
        self._refresh_hands()
        if not self._round.is_player_turn:
            # Wait until the page is on screen so the player sees the cards behind the message.
            self.after_idle(self._player_reached_twenty_one)

    def _hand_area(self, title: str):
        header = tk.Frame(self, bg=TABLE_GREEN)
        header.pack(fill=tk.X, padx=65, pady=(16, 4))
        _label(header, title).pack(side=tk.LEFT)
        sum_label = _label(header)
        sum_label.pack(side=tk.RIGHT)
        cards = tk.Frame(self, bg=TABLE_GREEN, height=134)
        cards.pack(fill=tk.X, padx=65)
        cards.pack_propagate(False)
        return cards, sum_label

    def _refresh_hands(self) -> None:
        self._show_hand(self._round.dealer, self._dealer_cards, self._dealer_sum)
        self._show_hand(self._player, self._player_cards, self._player_sum)

    def _show_hand(self, participant: Participant, cards_frame: tk.Frame, sum_label: tk.Label) -> None:
        for card in participant.hand.cards[len(cards_frame.winfo_children()):]:
            image = self._card_images.get(card)
            tk.Label(cards_frame, image=image, bg=TABLE_GREEN).pack(side=tk.LEFT, padx=3, pady=12)
        sum_label.config(text=f"Sum = {participant.hand.total}")

    def _hit(self) -> None:
        self._round.hit()
        self._refresh_hands()
        if self._round.is_over:
            self._end_round()
        elif not self._round.is_player_turn:
            self._player_reached_twenty_one()

    def _stand(self) -> None:
        self._round.stand()
        self._start_dealer_turn()

    def _player_reached_twenty_one(self) -> None:
        messagebox.showinfo("Blackjack", "Blackjack!")
        self._start_dealer_turn()

    def _start_dealer_turn(self) -> None:
        self._hit_button.config(state=tk.DISABLED)
        self._stand_button.config(state=tk.DISABLED)
        self.after(DEALER_TURN_DELAY_MS, self._dealer_step)

    def _dealer_step(self) -> None:
        card = self._round.dealer_step()
        self._refresh_hands()
        if card is None:
            self._end_round()
        else:
            self.after(DEALER_TURN_DELAY_MS, self._dealer_step)

    def _end_round(self) -> None:
        outcome: Optional[Outcome] = self._round.outcome
        assert outcome is not None
        messagebox.showinfo("Blackjack", outcome.value)
        self._on_round_over(self._player)


class BlackjackApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Blackjack")
        self.geometry("792x530")
        self.minsize(792, 530)
        self.configure(bg=TABLE_GREEN)
        self._card_images = CardImages()
        self._page: Optional[tk.Frame] = None

        icon = tk.PhotoImage(file=str(CARD_IMAGES_DIR / "ace_of_spades.png")).subsample(14)
        self.iconphoto(True, icon)

        self.show_welcome_page()

    def _show(self, page: tk.Frame) -> None:
        if self._page is not None:
            self._page.destroy()
        self._page = page
        page.pack(fill=tk.BOTH, expand=True)

    def show_welcome_page(self) -> None:
        self._show(WelcomePage(self, on_play=self.show_betting_page))

    def show_betting_page(self, player: Player) -> None:
        self._show(
            BettingPage(
                self,
                player,
                on_bet=lambda bet: self.show_game_page(player, bet),
                on_restart=self.show_welcome_page,
            )
        )

    def show_game_page(self, player: Player, bet: int) -> None:
        self._show(GamePage(self, player, bet, self._card_images, on_round_over=self.show_betting_page))


def main() -> None:
    BlackjackApp().mainloop()
