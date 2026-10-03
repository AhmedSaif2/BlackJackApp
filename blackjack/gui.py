"""Tkinter front-end: welcome page -> betting page -> game page."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Dict, List, Optional, Tuple

from .cards import Card, Suit
from .game import BET_OPTIONS, STARTING_POCKET_MONEY, Outcome, Round
from .hand import Hand
from .participants import Dealer, Participant, Player

CARD_IMAGES_DIR = Path(__file__).parent / "assets" / "playing_cards"
# The source images are 500x726; shrinking by 7 gives roughly 72x104 cards on screen.
CARD_IMAGE_SUBSAMPLE = 7
DEALER_TURN_DELAY_MS = 1000
# A dealt card slides from the deck to its place in the hand, flipping face up on the way.
DEAL_ANIMATION_MS = 400
DEAL_ANIMATION_FRAME_MS = 15

TABLE_GREEN = "#2e8b57"  # SeaGreen, as in the original WinForms app
TEXT_COLOR = "white"
CARD_BACK_COLOR = "#1f3c88"
CARD_BACK_TRIM = "#6a8cd8"
TITLE_FONT = ("Segoe UI", 36)
LABEL_FONT = ("Segoe UI", 20)
BUTTON_FONT = ("Segoe UI", 15)


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

    def back(self) -> tk.PhotoImage:
        """A plain card back the same size as the faces (the assets have no back image)."""
        if "back" not in self._cache:
            width, height = self._size()
            image = tk.PhotoImage(width=width, height=height)
            image.put("white", to=(0, 0, width, height))
            image.put(CARD_BACK_TRIM, to=(4, 4, width - 4, height - 4))
            image.put(CARD_BACK_COLOR, to=(7, 7, width - 7, height - 7))
            self._cache["back"] = image
        return self._cache["back"]

    def blank(self) -> tk.PhotoImage:
        """A transparent card-sized image that holds a card's spot while it's in flight."""
        if "blank" not in self._cache:
            width, height = self._size()
            self._cache["blank"] = tk.PhotoImage(width=width, height=height)
        return self._cache["blank"]

    def _size(self) -> Tuple[int, int]:
        face = self.get(Card("ace", Suit.SPADE))
        return face.width(), face.height()


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

        # The deck sits below the hands, in the gap between the buttons and the bet.
        self._deck = tk.Label(self, image=card_images.back(), bg=TABLE_GREEN)
        self._deck.place(relx=0.5, rely=1.0, anchor=tk.S, y=-10)

        self._round = Round(player, Dealer(), bet)
        # How many of each hand's cards have been dealt onto the table so far.
        self._shown: Dict[tk.Frame, int] = {self._dealer_cards: 0, self._player_cards: 0}
        self._set_buttons_enabled(False)
        # Wait until the page is on screen and laid out, so the cards have somewhere to fly to.
        self.after_idle(lambda: self._deal_new_cards(then=self._after_player_card))

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

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self._hit_button.config(state=state)
        self._stand_button.config(state=state)

    def _deal_new_cards(self, then: Callable[[], None]) -> None:
        """Animate each card that isn't on the table yet, one at a time, then call ``then``.

        The player's cards go first, the same order ``Round`` deals the opening hand in.
        """
        hands: List[Tuple[Participant, tk.Frame, tk.Label]] = [
            (self._player, self._player_cards, self._player_sum),
            (self._round.dealer, self._dealer_cards, self._dealer_sum),
        ]
        for participant, cards_frame, sum_label in hands:
            if self._shown[cards_frame] < len(participant.hand):
                self._deal_card(participant, cards_frame, sum_label, then=lambda: self._deal_new_cards(then))
                return
        then()

    def _deal_card(
        self, participant: Participant, cards_frame: tk.Frame, sum_label: tk.Label, then: Callable[[], None]
    ) -> None:
        index = self._shown[cards_frame]
        self._shown[cards_frame] = index + 1
        dealt = participant.hand.cards[: index + 1]
        face, back = self._card_images.get(dealt[-1]), self._card_images.back()

        # Hold the card's spot in the hand open so we know where it lands.
        slot = tk.Label(cards_frame, image=self._card_images.blank(), bg=TABLE_GREEN)
        slot.pack(side=tk.LEFT, padx=3, pady=12)
        self.update_idletasks()
        start_x, start_y = self._deck.winfo_x(), self._deck.winfo_y()
        end_x, end_y = cards_frame.winfo_x() + slot.winfo_x(), cards_frame.winfo_y() + slot.winfo_y()
        width = slot.winfo_width()

        flyer = tk.Label(self, image=back, bg=TABLE_GREEN)
        steps = max(1, DEAL_ANIMATION_MS // DEAL_ANIMATION_FRAME_MS)

        def land() -> None:
            flyer.destroy()
            slot.config(image=face)
            # Only count the card once it's on the table.
            hand = Hand()
            for card in dealt:
                hand.add_card(card)
            sum_label.config(text=f"Sum = {hand.total}")
            then()

        def move(step: int) -> None:
            t = step / steps
            eased = 1 - (1 - t) ** 3
            # Flip during the second half: squeeze the back down to nothing, then widen the face.
            flip = max(0.0, 2 * t - 1)
            visible = max(1, round(width * abs(1 - 2 * flip)))
            flyer.config(image=back if flip < 0.5 else face)
            flyer.place(
                x=round(start_x + (end_x - start_x) * eased + (width - visible) / 2),
                y=round(start_y + (end_y - start_y) * eased),
                width=visible,
            )
            if step < steps:
                self.after(DEAL_ANIMATION_FRAME_MS, move, step + 1)
            else:
                land()

        move(0)

    def _after_player_card(self) -> None:
        if self._round.is_over:
            self._end_round()
        elif self._round.is_player_turn:
            self._set_buttons_enabled(True)
        else:
            self._player_reached_twenty_one()

    def _hit(self) -> None:
        self._set_buttons_enabled(False)
        self._round.hit()
        self._deal_new_cards(then=self._after_player_card)

    def _stand(self) -> None:
        self._round.stand()
        self._start_dealer_turn()

    def _player_reached_twenty_one(self) -> None:
        messagebox.showinfo("Blackjack", "Blackjack!")
        self._start_dealer_turn()

    def _start_dealer_turn(self) -> None:
        self._set_buttons_enabled(False)
        self.after(DEALER_TURN_DELAY_MS, self._dealer_step)

    def _dealer_step(self) -> None:
        if self._round.dealer_step() is None:
            self._end_round()
        else:
            self._deal_new_cards(then=lambda: self.after(DEALER_TURN_DELAY_MS, self._dealer_step))

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
