"""Tkinter front-end: a single table where you bet, play and see the results."""

from __future__ import annotations

import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Dict, List, Optional, Tuple

from .cards import Card, Suit
from .game import BET_OPTIONS, Outcome, Round, new_player
from .hand import Hand
from .participants import Dealer, Participant, Player
from .save import SaveFile

CARD_IMAGES_DIR = Path(__file__).parent / "assets" / "playing_cards"
# The source images are 500x726; shrinking by 7 gives roughly 72x104 cards on screen.
CARD_IMAGE_SUBSAMPLE = 7
DEALER_TURN_DELAY_MS = 1000
# A dealt card slides from the deck to its place in the hand, flipping face up on the way.
DEAL_ANIMATION_MS = 400
DEAL_ANIMATION_FRAME_MS = 15
# How often to check whether the dealer (Jev) has made its decision.
DEALER_POLL_MS = 50

TABLE_GREEN = "#2e8b57"  # SeaGreen, as in the original WinForms app
TEXT_COLOR = "white"
WIN_COLOR = "#ffd700"
LOSE_COLOR = "#ffc4c4"
HINT_COLOR = "#cfe8d9"
CARD_BACK_COLOR = "#1f3c88"
CARD_BACK_TRIM = "#6a8cd8"
LABEL_FONT = ("Segoe UI", 20)
BANNER_FONT = ("Segoe UI", 20, "bold")
BUTTON_FONT = ("Segoe UI", 15)
SCOREBOARD_FONT = ("Segoe UI", 11)

KEYS_HINT = "Keys: 1 / 2 / 3 bet  ·  Enter same bet  ·  H hit  ·  S stand"


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


def _label(parent: tk.Misc, text: str = "", font=LABEL_FONT, fg: str = TEXT_COLOR) -> tk.Label:
    return tk.Label(parent, text=text, font=font, bg=TABLE_GREEN, fg=fg)


def _button(parent: tk.Misc, text: str, command: Callable[[], None], underline: int = -1) -> tk.Button:
    return tk.Button(parent, text=text, font=BUTTON_FONT, width=8, bg="white", command=command, underline=underline)


def result_banner(game: Round) -> Tuple[str, str]:
    """The text and colour announcing how a finished round went."""
    bet = game.bet
    if game.outcome is Outcome.WIN:
        return (f"Blackjack! You win +{bet}$" if game.is_blackjack else f"You win! +{bet}$"), WIN_COLOR
    if game.outcome is Outcome.DRAW:
        return "Push. Your bet is returned", TEXT_COLOR
    if game.player.hand.is_bust():
        return f"Bust! -{bet}$", LOSE_COLOR
    return f"Dealer wins. -{bet}$", LOSE_COLOR


# One background thread runs the dealer's decisions, one at a time.
_dealer_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dealer")


class Table(tk.Frame):
    """The whole game on one screen.

    Between rounds the bet buttons sit under the hands, and the last hand stays on the
    table so you can see how it went. Placing a bet deals a new hand and swaps the bet
    buttons for Hit and Stand. Your chips and stats are saved as you play.
    """

    def __init__(self, master: tk.Misc, player: Player, save: SaveFile, card_images: CardImages):
        super().__init__(master, bg=TABLE_GREEN)
        self.player = player
        self._save = save
        self._card_images = card_images
        self._round: Optional[Round] = None
        self._last_bet: Optional[int] = None

        top = tk.Frame(self, bg=TABLE_GREEN)
        top.pack(fill=tk.X, padx=40, pady=(14, 0))
        self._chips_label = _label(top, font=BUTTON_FONT)
        self._chips_label.pack(side=tk.LEFT)
        self._bet_label = _label(top, font=BUTTON_FONT)
        self._bet_label.pack(side=tk.RIGHT)
        self.banner = _label(top, font=BANNER_FONT)
        self.banner.pack(side=tk.LEFT, expand=True)

        self.dealer_cards, self._dealer_sum = self._hand_area("Dealer")
        self.player_cards, self._player_sum = self._hand_area("You")
        # How many of each hand's cards have been dealt onto the table so far.
        self._shown: Dict[tk.Frame, int] = {self.dealer_cards: 0, self.player_cards: 0}

        controls = tk.Frame(self, bg=TABLE_GREEN, height=60)
        controls.pack(fill=tk.X, padx=65, pady=(14, 0))
        controls.pack_propagate(False)
        self._bet_row = tk.Frame(controls, bg=TABLE_GREEN)
        self.bet_buttons: Dict[int, tk.Button] = {}
        _label(self._bet_row, "Bet", BUTTON_FONT).pack(side=tk.LEFT, padx=(0, 20))
        for bet in BET_OPTIONS:
            button = _button(self._bet_row, f"{bet}$", lambda bet=bet: self._deal(bet))
            button.pack(side=tk.LEFT, padx=12)
            self.bet_buttons[bet] = button
        self._play_row = tk.Frame(controls, bg=TABLE_GREEN)
        self.hit_button = _button(self._play_row, "Hit", self._hit, underline=0)
        self.hit_button.pack(side=tk.LEFT, padx=12)
        self.stand_button = _button(self._play_row, "Stand", self._stand, underline=0)
        self.stand_button.pack(side=tk.LEFT, padx=12)
        self._broke_row = tk.Frame(controls, bg=TABLE_GREEN)
        _label(self._broke_row, "You're out of chips.", BUTTON_FONT).pack(side=tk.LEFT, padx=(0, 20))
        self.start_over_button = _button(self._broke_row, "Start over", self._start_new_game)
        self.start_over_button.pack(side=tk.LEFT)

        bottom = tk.Frame(self, bg=TABLE_GREEN)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=(0, 12))
        self.new_game_button = tk.Button(
            bottom, text="New game", font=SCOREBOARD_FONT, bg="white", command=self._confirm_new_game
        )
        self.new_game_button.pack(side=tk.RIGHT, anchor=tk.S)
        self.stats_lines = [_label(bottom, font=SCOREBOARD_FONT, fg=HINT_COLOR) for _ in range(2)]
        for line in self.stats_lines:
            line.pack(anchor=tk.W)
        _label(bottom, KEYS_HINT, SCOREBOARD_FONT, fg=HINT_COLOR).pack(anchor=tk.W)

        # The deck sits at the dealer's right, like a shoe.
        self._deck = tk.Label(self, image=card_images.back(), bg=TABLE_GREEN)
        self._deck.place(relx=1.0, x=-30, y=104, anchor=tk.NE)

        toplevel = self.winfo_toplevel()
        for key, button in (("h", self.hit_button), ("s", self.stand_button)):
            for keysym in (key, key.upper()):
                toplevel.bind(f"<KeyPress-{keysym}>", lambda _event, button=button: self._press(button))
        for number, bet in enumerate(BET_OPTIONS, start=1):
            toplevel.bind(f"<KeyPress-{number}>", lambda _event, bet=bet: self._press(self.bet_buttons[bet]))
        toplevel.bind("<Return>", lambda _event: self._press_same_bet())

        self._between_rounds("Welcome back!" if player.stats.rounds_played else "Place your bet", TEXT_COLOR)

    # --- Layout helpers ---

    def _hand_area(self, title: str):
        header = tk.Frame(self, bg=TABLE_GREEN)
        header.pack(fill=tk.X, padx=65, pady=(10, 0))
        _label(header, title).pack(side=tk.LEFT)
        sum_label = _label(header)
        sum_label.pack(side=tk.LEFT, padx=20)
        cards = tk.Frame(self, bg=TABLE_GREEN, height=128)
        cards.pack(fill=tk.X, padx=65)
        cards.pack_propagate(False)
        return cards, sum_label

    def _show_row(self, row: tk.Frame) -> None:
        for other in (self._bet_row, self._play_row, self._broke_row):
            if other is not row:
                other.pack_forget()
        row.pack(side=tk.LEFT)

    def _set_play_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.hit_button.config(state=state)
        self.stand_button.config(state=state)

    def _round_in_progress(self) -> bool:
        return self._round is not None and not self._round.is_over

    def _refresh_status(self) -> None:
        self._chips_label.config(text=f"Chips: {self.player.pocket_money}$")
        self._bet_label.config(text=f"Bet: {self._round.bet}$" if self._round_in_progress() else "")
        self.new_game_button.config(state=tk.DISABLED if self._round_in_progress() else tk.NORMAL)
        stats = self.player.stats
        lines = stats.summary_lines() if stats.rounds_played else ["No hands played yet", ""]
        for label, text in zip(self.stats_lines, lines):
            label.config(text=text)

    def _press(self, button: tk.Button) -> None:
        """Keyboard shortcut: click ``button`` if it's on screen and enabled."""
        if button.winfo_manager() and button.master.winfo_manager() and str(button.cget("state")) == tk.NORMAL:
            button.invoke()

    def _press_same_bet(self) -> None:
        if self._last_bet is not None:
            self._press(self.bet_buttons[self._last_bet])

    # --- Between rounds ---

    def _between_rounds(self, banner: str, colour: str) -> None:
        self.banner.config(text=banner, fg=colour)
        self._refresh_status()
        if not any(self.player.can_afford(bet) for bet in BET_OPTIONS):
            self._show_row(self._broke_row)
            return
        for bet, button in self.bet_buttons.items():
            button.config(state=tk.NORMAL if self.player.can_afford(bet) else tk.DISABLED)
        self._show_row(self._bet_row)

    def _confirm_new_game(self) -> None:
        if self._round_in_progress():
            return
        if messagebox.askyesno("Blackjack", "Start a new game? Your chips and stats will be reset."):
            self._start_new_game()

    def _start_new_game(self) -> None:
        self.player = new_player()
        self._round = None
        self._last_bet = None
        self._save.save(self.player)
        self._clear_table()
        self._between_rounds("New game. Place your bet", TEXT_COLOR)

    def _clear_table(self) -> None:
        for cards_frame, sum_label in ((self.dealer_cards, self._dealer_sum), (self.player_cards, self._player_sum)):
            for child in cards_frame.winfo_children():
                child.destroy()
            self._shown[cards_frame] = 0
            sum_label.config(text="")

    # --- Playing a round ---

    def _deal(self, bet: int) -> None:
        self._clear_table()
        self._last_bet = bet
        self._round = Round(self.player, Dealer(), bet)
        # Save once the bet is down, so closing the window mid-hand doesn't undo a losing hand.
        self._save.save(self.player)
        self.banner.config(text="")
        self._refresh_status()
        self._set_play_buttons_enabled(False)
        self._show_row(self._play_row)
        # Wait until the table is laid out, so the cards have somewhere to fly to.
        self.after_idle(lambda: self._deal_new_cards(then=self._after_player_card))

    def _deal_new_cards(self, then: Callable[[], None]) -> None:
        """Animate each card that isn't on the table yet, one at a time, then call ``then``.

        The player's cards go first, the same order ``Round`` deals the opening hand in.
        """
        assert self._round is not None
        hands: List[Tuple[Participant, tk.Frame, tk.Label]] = [
            (self.player, self.player_cards, self._player_sum),
            (self._round.dealer, self.dealer_cards, self._dealer_sum),
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
            sum_label.config(text=f"{hand.total}" + (" Bust" if hand.is_bust() else ""))
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
        assert self._round is not None
        if self._round.is_over:
            self._end_round()
        elif self._round.is_player_turn:
            self._set_play_buttons_enabled(True)
        else:
            # The player reached 21, so their turn is over.
            self.banner.config(text="Blackjack!" if self._round.is_blackjack else "21!", fg=WIN_COLOR)
            self._start_dealer_turn()

    def _hit(self) -> None:
        assert self._round is not None
        self._set_play_buttons_enabled(False)
        self._round.hit()
        self._deal_new_cards(then=self._after_player_card)

    def _stand(self) -> None:
        assert self._round is not None
        self._round.stand()
        self._start_dealer_turn()

    def _start_dealer_turn(self) -> None:
        self._set_play_buttons_enabled(False)
        self.after(DEALER_TURN_DELAY_MS, self._dealer_step)

    def _dealer_step(self) -> None:
        assert self._round is not None
        # The dealer asks Jev over the network, so decide off the Tk thread to keep the window responsive.
        self._wait_for_dealer(_dealer_worker.submit(self._round.dealer_step))

    def _wait_for_dealer(self, decision: Future[Optional[Card]]) -> None:
        if not decision.done():
            self.after(DEALER_POLL_MS, self._wait_for_dealer, decision)
            return
        if not self.winfo_exists():
            return
        if decision.result() is None:
            self._end_round()
        else:
            self._deal_new_cards(then=lambda: self.after(DEALER_TURN_DELAY_MS, self._dealer_step))

    def _end_round(self) -> None:
        assert self._round is not None
        self._save.save(self.player)
        self._between_rounds(*result_banner(self._round))


class BlackjackApp(tk.Tk):
    def __init__(self, save: Optional[SaveFile] = None) -> None:
        super().__init__()
        self.title("Blackjack")
        self.geometry("792x600")
        self.minsize(792, 600)
        self.configure(bg=TABLE_GREEN)
        save = save if save is not None else SaveFile()

        icon = tk.PhotoImage(file=str(CARD_IMAGES_DIR / "ace_of_spades.png")).subsample(14)
        self.iconphoto(True, icon)

        self.table = Table(self, save.load(), save, CardImages())
        self.table.pack(fill=tk.BOTH, expand=True)


def main() -> None:
    BlackjackApp().mainloop()
