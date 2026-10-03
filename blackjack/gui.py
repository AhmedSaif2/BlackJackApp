"""Tkinter front-end: a single table where you bet, play and see the results."""

from __future__ import annotations

import math
import random
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Dict, List, Optional, Set, Tuple

from .cards import Card, Suit
from .game import BET_OPTIONS, Outcome, Round, new_player
from .hand import Hand
from .participants import Dealer, Participant, Player
from .save import SaveFile

CARD_IMAGES_DIR = Path(__file__).parent / "assets" / "playing_cards"
# The source images are 500x726; shrinking by 7 gives roughly 72x104 cards on screen.
CARD_IMAGE_SUBSAMPLE = 7
DEALER_TURN_DELAY_MS = 1000
# How often to check whether the dealer (Jev) has made its decision.
DEALER_POLL_MS = 50

# Animation timings.
ANIMATION_FRAME_MS = 15
# A dealt card arcs from the deck to its place in the hand, turning face up on the way.
DEAL_ANIMATION_MS = 450
DEAL_ARC_HEIGHT = 45
# A hand's total flashes gold when it changes.
SUM_FLASH_FRAMES = 12
SUM_FLASH_FRAME_MS = 40
# Result banners pop in over the table; "Blackjack!" clears itself and the round carries on.
BANNER_INTRO_MS = 450
BLACKJACK_BANNER_MS = 1300
CONFETTI_MS = 3000
CONFETTI_PER_BURST = 70

# Table layout (canvas coordinates; cards are 72x104). A status bar sits below the table.
TABLE_WIDTH, TABLE_HEIGHT = 792, 530
TABLE_MARGIN_X = 65
DEALER_TITLE_Y, DEALER_CARDS_Y = 36, 60
PLAYER_TITLE_Y, PLAYER_CARDS_Y = 206, 230
CONTROLS_Y = 400
BET_X = 470
CARD_STEP = 80
MAX_SPREAD_CARDS = 7
CARD_OVERLAP_STEP = 24
# The deck sits bottom right, like a dealer's shoe, so cards fly away from the buttons.
DECK_X, DECK_Y = 650, 360
DECK_DEPTH = 3
SHADOW_OFFSET = 4
# Banners cover the controls row, leaving both hands in view. Between rounds they hold the bet buttons.
BANNER_Y = 425
BANNER_BUTTONS_Y = BANNER_Y + 48
BANNER_WIDTH, BANNER_HEIGHT = 440, 150

TABLE_GREEN = "#2e8b57"  # SeaGreen, as in the original WinForms app
SHADOW_COLOR = "#1d5e3a"
TEXT_COLOR = "#ffffff"
HINT_COLOR = "#cfe8d9"
HIGHLIGHT_COLOR = "#ffd54f"
BUST_COLOR = "#ff8a80"
CARD_BACK_COLOR = "#1f3c88"
CARD_BACK_ALT = "#2c55b0"
CARD_BACK_TRIM = "#8fb0f0"
LABEL_FONT = ("Segoe UI", 20)
BUTTON_FONT = ("Segoe UI", 15)
SCOREBOARD_FONT = ("Segoe UI", 11)
BANNER_FONT = ("Segoe UI", 38)
# Mid-flip card frames are made in steps of this many pixels wide.
SQUEEZE_STEP = 6
MAX_SQUEEZED_IMAGES = 150

KEYS_HINT = "Keys: 1 / 2 / 3 bet  ·  Enter same bet  ·  H hit  ·  S stand"


class CardImages:
    """Loads card images on first use and keeps references so Tk doesn't drop them."""

    def __init__(self) -> None:
        self._cache: Dict[str, tk.PhotoImage] = {}
        # Mid-flip frames, made on demand and dropped when there get to be too many.
        self._squeezed: Dict[str, tk.PhotoImage] = {}

    def get(self, card: Card) -> tk.PhotoImage:
        name = card.image_name
        if name not in self._cache:
            image = tk.PhotoImage(file=str(CARD_IMAGES_DIR / f"{name}.png"))
            self._cache[name] = image.subsample(CARD_IMAGE_SUBSAMPLE)
        return self._cache[name]

    def back(self) -> tk.PhotoImage:
        """A patterned card back the same size as the faces (the assets have no back image)."""
        if "back" not in self._cache:
            width, height = self.size()
            rows = []
            for y in range(height):
                row = []
                for x in range(width):
                    edge = min(x, y, width - 1 - x, height - 1 - y)
                    if edge < 3:
                        color = "#ffffff"
                    elif edge < 5 or edge == 6:
                        color = CARD_BACK_COLOR
                    elif edge == 5:
                        color = CARD_BACK_TRIM
                    else:
                        # A diamond lattice, like a classic deck.
                        color = CARD_BACK_ALT if ((x + y) // 6 + (x - y + height) // 6) % 2 else CARD_BACK_COLOR
                    row.append(color)
                rows.append("{" + " ".join(row) + "}")
            image = tk.PhotoImage(width=width, height=height)
            image.put(" ".join(rows))
            self._cache["back"] = image
        return self._cache["back"]

    def squeezed(self, card: Optional[Card], width: int) -> tk.PhotoImage:
        """``card``'s face (or the back, for None) squeezed to ``width``, as it looks mid-flip."""
        source = self.back() if card is None else self.get(card)
        full_width, height = source.width(), source.height()
        # Snap to a few widths so a flip reuses the same handful of frames.
        width = min(full_width, max(2, width // SQUEEZE_STEP * SQUEEZE_STEP))
        if width == full_width:
            return source
        key = f"{card.image_name if card else 'back'}@{width}"
        if key not in self._squeezed:
            if len(self._squeezed) > MAX_SQUEEZED_IMAGES:
                self._squeezed.clear()
            image = tk.PhotoImage(width=width, height=height)
            for column in range(width):
                source_column = int((column + 0.5) * full_width / width)
                image.tk.call(image, "copy", source, "-from", source_column, 0, source_column + 1, height, "-to", column, 0)
            self._squeezed[key] = image
        return self._squeezed[key]

    def size(self) -> Tuple[int, int]:
        face = self.get(Card("ace", Suit.SPADE))
        return face.width(), face.height()


def _label(parent: tk.Misc, text: str = "", font=LABEL_FONT, fg: str = TEXT_COLOR) -> tk.Label:
    return tk.Label(parent, text=text, font=font, bg=TABLE_GREEN, fg=fg)


def _button(parent: tk.Misc, text: str, command: Callable[[], None], underline: int = -1) -> tk.Button:
    return tk.Button(parent, text=text, font=BUTTON_FONT, width=8, bg="white", command=command, underline=underline)


# One background thread runs the dealer's decisions, one at a time.
_dealer_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dealer")

# Banner looks: (panel fill, panel outline, title colour, subtitle colour).
BANNER_STYLES = {
    "win": ("#f5c518", "#fff3b0", "#3b2a00", "#5c4300"),
    "lose": ("#8b1e2d", "#d9727f", "white", "#f3c9cf"),
    "draw": ("#37474f", "#90a4ae", "white", "#cfd8dc"),
    "table": ("#226b45", "#7fc8a0", "white", "#cfe8d9"),
}
CONFETTI_COLORS = ("#f5c518", "#ff5252", "#40c4ff", "#69f0ae", "#e040fb", "#ffffff", "#ff9100")


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def _ease_out_back(t: float) -> float:
    """Overshoots a little past 1 before settling, for a "pop"."""
    c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def _blend(start: str, end: str, t: float) -> str:
    """Mix two ``#rrggbb`` colours; ``t`` = 0 gives ``start``, 1 gives ``end``."""
    a = [int(start[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(end[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


class Table(tk.Frame):
    """The whole game on one screen, drawn on a canvas so cards can fly, flip and be celebrated over.

    Between rounds a banner on the table holds the bet buttons (after a round, it also
    announces the result) and the last hand stays in view. Placing a bet clears the
    table and deals a new hand. Your chips and stats are saved as you play.
    """

    def __init__(self, master: tk.Misc, player: Player, save: SaveFile, card_images: CardImages):
        super().__init__(master, bg=TABLE_GREEN)
        self.player = player
        self._save = save
        self._card_images = card_images
        self._round: Optional[Round] = None
        self._last_bet: Optional[int] = None
        # True while the bet buttons are on offer in the banner.
        self._accepting_bets = False
        # Animation callbacks still waiting to run; cancelled when the table is cleared or closed.
        self._pending: Set[str] = set()

        # Under the table: the scoreboard and a key hint, with your chips and New game on the right.
        status = tk.Frame(self, bg=TABLE_GREEN)
        status.pack(side=tk.BOTTOM, fill=tk.X, padx=TABLE_MARGIN_X - 25, pady=(0, 10))
        right_column = tk.Frame(status, bg=TABLE_GREEN)
        right_column.pack(side=tk.RIGHT, anchor=tk.S)
        self._chips_label = _label(right_column, font=BUTTON_FONT)
        self._chips_label.pack(anchor=tk.E)
        self.new_game_button = tk.Button(
            right_column, text="New game", font=SCOREBOARD_FONT, bg="white", command=self._confirm_new_game
        )
        self.new_game_button.pack(anchor=tk.E, pady=(4, 0))
        self.stats_lines = [_label(status, font=SCOREBOARD_FONT, fg=HINT_COLOR) for _ in range(2)]
        for line in self.stats_lines:
            line.pack(anchor=tk.W)
        _label(status, KEYS_HINT, SCOREBOARD_FONT, fg=HINT_COLOR).pack(anchor=tk.W)

        # A fixed-size table, kept centred if the window is made bigger.
        self._table = tk.Canvas(self, width=TABLE_WIDTH, height=TABLE_HEIGHT, bg=TABLE_GREEN, highlightthickness=0)
        self._table.pack(expand=True)
        right = TABLE_WIDTH - TABLE_MARGIN_X
        self._sum_text: Dict[str, int] = {}
        for key, title, title_y in (("dealer", "Dealer Cards", DEALER_TITLE_Y), ("player", "Your Cards", PLAYER_TITLE_Y)):
            self._table.create_text(TABLE_MARGIN_X, title_y, text=title, font=LABEL_FONT, fill=TEXT_COLOR, anchor=tk.W)
            self._sum_text[key] = self._table.create_text(right, title_y, text="", font=LABEL_FONT, fill=TEXT_COLOR, anchor=tk.E)
        self._bet_text = self._table.create_text(BET_X, CONTROLS_Y, text="", font=LABEL_FONT, fill=TEXT_COLOR)

        self.hit_button = _button(self._table, "Hit", self._hit, underline=0)
        self.stand_button = _button(self._table, "Stand", self._stand, underline=0)
        self._controls = [
            self._table.create_window(TABLE_MARGIN_X + 25, CONTROLS_Y, window=self.hit_button, anchor=tk.W),
            self._table.create_window(TABLE_MARGIN_X + 145, CONTROLS_Y, window=self.stand_button, anchor=tk.W),
        ]
        self._hide_controls()

        # The deck: a few backs stacked with a slight offset, so it reads as a pile.
        for depth in range(DECK_DEPTH, 0, -1):
            self._table.create_image(DECK_X + depth * 2, DECK_Y + depth * 2, image=card_images.back(), anchor=tk.NW)
        self._table.create_image(DECK_X, DECK_Y, image=card_images.back(), anchor=tk.NW)
        # Canvas items of the cards that have landed in each hand.
        self._cards: Dict[str, List[int]] = {"dealer": [], "player": []}

        # What a banner offers between rounds: the bets, or Start over once you're out of chips.
        self._bet_row = tk.Frame(self._table)
        self.bet_buttons: Dict[int, tk.Button] = {}
        for bet in BET_OPTIONS:
            button = _button(self._bet_row, f"{bet}$", lambda bet=bet: self._deal(bet))
            button.pack(side=tk.LEFT, padx=8)
            self.bet_buttons[bet] = button
        self._start_over_row = tk.Frame(self._table)
        self.start_over_button = _button(self._start_over_row, "Start over", self._start_new_game)
        self.start_over_button.pack()

        toplevel = self.winfo_toplevel()
        for key, button in (("h", self.hit_button), ("s", self.stand_button)):
            for keysym in (key, key.upper()):
                toplevel.bind(f"<KeyPress-{keysym}>", lambda _event, button=button: self._press(button))
        for number, bet in enumerate(BET_OPTIONS, start=1):
            toplevel.bind(f"<KeyPress-{number}>", lambda _event, bet=bet: self._press(self.bet_buttons[bet]))
        toplevel.bind("<Return>", lambda _event: self._press_same_bet())

        self._refresh_status()
        if self._is_broke():
            self._open_betting("Out of chips", "Start over to play again", "lose")
        elif player.stats.rounds_played:
            self._open_betting("Welcome back!", "Place your bet", "table")
        else:
            self._open_betting("Blackjack", "Place your bet", "table")

    def _later(self, ms: int, callback: Callable[..., None], *args) -> None:
        """``after``, cancelled if the table is cleared or closed first (say, a new bet mid-confetti)."""

        def run() -> None:
            self._pending.discard(after_id)
            callback(*args)

        after_id = self.after(ms, run)
        self._pending.add(after_id)

    def _cancel_pending(self) -> None:
        for after_id in self._pending:
            self.after_cancel(after_id)
        self._pending.clear()

    def destroy(self) -> None:
        self._cancel_pending()
        super().destroy()

    def _hide_controls(self) -> None:
        """Once the player's turn is over, clear the buttons away to make room for banners."""
        self._set_buttons_enabled(False)
        for control in self._controls:
            self._table.itemconfigure(control, state=tk.HIDDEN)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.hit_button.config(state=state)
        self.stand_button.config(state=state)

    # --- Status and shortcuts -------------------------------------------------------------

    def _is_broke(self) -> bool:
        return not any(self.player.can_afford(bet) for bet in BET_OPTIONS)

    def _round_in_progress(self) -> bool:
        return self._round is not None and not self._round.is_over

    def _refresh_status(self) -> None:
        self._chips_label.config(text=f"Chips: {self.player.pocket_money}$")
        self.new_game_button.config(state=tk.DISABLED if self._round_in_progress() else tk.NORMAL)
        stats = self.player.stats
        lines = stats.summary_lines() if stats.rounds_played else ["No hands played yet", ""]
        for label, text in zip(self.stats_lines, lines):
            label.config(text=text)

    def _press(self, button: tk.Button) -> None:
        """Keyboard shortcut: click ``button`` if it's enabled (bets also need to be on offer)."""
        if str(button.cget("state")) == tk.NORMAL:
            button.invoke()

    def _press_same_bet(self) -> None:
        if self._last_bet is not None:
            self._press(self.bet_buttons[self._last_bet])

    # --- Between rounds -------------------------------------------------------------------

    def _open_betting(self, title: str, subtitle: str, style: str) -> None:
        self._show_banner(title, subtitle, style, then=lambda: self._offer_bets(style))

    def _offer_bets(self, style: str) -> None:
        """Put the bet buttons (or Start over, when you're out of chips) in the banner."""
        row = self._start_over_row if self._is_broke() else self._bet_row
        row.config(bg=BANNER_STYLES[style][0])
        if row is self._bet_row:
            for bet, button in self.bet_buttons.items():
                button.config(state=tk.NORMAL if self.player.can_afford(bet) else tk.DISABLED)
            self._accepting_bets = True
        self._table.create_window(TABLE_WIDTH / 2, BANNER_BUTTONS_Y, window=row, tags=("banner", "round"))

    def _clear_table(self) -> None:
        """Sweep the last hand, its banner and any animation still running off the table."""
        self._cancel_pending()
        self._accepting_bets = False
        self._table.delete("round")
        self._cards = {"dealer": [], "player": []}
        for item in self._sum_text.values():
            self._table.itemconfigure(item, text="", fill=TEXT_COLOR)
        self._table.itemconfigure(self._bet_text, text="")

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
        self._hide_controls()
        self._refresh_status()
        self._open_betting("New game", "Place your bet", "table")

    # --- Playing a round ------------------------------------------------------------------

    def _deal(self, bet: int) -> None:
        if not self._accepting_bets or not self.player.can_afford(bet):
            return
        self._clear_table()
        self._last_bet = bet
        self._round = Round(self.player, Dealer(), bet)
        # Save once the bet is down, so closing the window mid-hand doesn't undo a losing hand.
        self._save.save(self.player)
        self._table.itemconfigure(self._bet_text, text=f"Bet = {bet}$")
        for control in self._controls:
            self._table.itemconfigure(control, state=tk.NORMAL)
        self._set_buttons_enabled(False)
        self._refresh_status()
        # Wait until the table is drawn, so the first card is seen leaving the deck.
        self._later(0, self._deal_new_cards, self._after_player_card)

    # --- Dealing ---------------------------------------------------------------------------

    def _deal_new_cards(self, then: Callable[[], None]) -> None:
        """Animate each card that isn't on the table yet, one at a time, then call ``then``.

        The player's cards go first, the same order ``Round`` deals the opening hand in.
        """
        for key, participant in (("player", self.player), ("dealer", self._round.dealer)):
            if len(self._cards[key]) < len(participant.hand):
                self._deal_card(key, participant, then=lambda: self._deal_new_cards(then))
                return
        then()

    def _card_position(self, key: str, index: int) -> Tuple[int, int]:
        # Cards sit side by side; a long hand overlaps its later cards so it stays on the table.
        x = TABLE_MARGIN_X + min(index, MAX_SPREAD_CARDS - 1) * CARD_STEP
        x += max(0, index - MAX_SPREAD_CARDS + 1) * CARD_OVERLAP_STEP
        return x, DEALER_CARDS_Y if key == "dealer" else PLAYER_CARDS_Y

    def _deal_card(self, key: str, participant: Participant, then: Callable[[], None]) -> None:
        """Fly the next card from the deck to its place: it arcs up off the table, casting a
        shadow, and turns face up on the way down."""
        index = len(self._cards[key])
        dealt = participant.hand.cards[: index + 1]
        card = dealt[-1]
        width, height = self._card_images.size()
        end_x, end_y = self._card_position(key, index)
        shadow = self._table.create_rectangle(0, 0, 0, 0, fill=SHADOW_COLOR, outline="", tags=("flying", "round"))
        flyer = self._table.create_image(DECK_X, DECK_Y, image=self._card_images.back(), anchor=tk.NW, tags=("flying", "round"))
        steps = max(1, DEAL_ANIMATION_MS // ANIMATION_FRAME_MS)

        def frame(step: int) -> None:
            t = step / steps
            eased = _ease_out_cubic(t)
            lift = DEAL_ARC_HEIGHT * math.sin(math.pi * t)
            x = DECK_X + (end_x - DECK_X) * eased
            y = DECK_Y + (end_y - DECK_Y) * eased - lift
            # Turn over between 30% and 80% of the flight: the back narrows to an edge, then the face widens.
            turn = min(1.0, max(0.0, (t - 0.3) / 0.5))
            visible = max(1, round(width * abs(math.cos(math.pi * turn))))
            image = self._card_images.squeezed(None if turn < 0.5 else card, visible)
            left = x + (width - image.width()) / 2
            self._table.itemconfigure(flyer, image=image)
            self._table.coords(flyer, left, y)
            # The higher the card, the further its shadow falls from it.
            offset = SHADOW_OFFSET + lift * 0.35
            self._table.coords(
                shadow, left + offset, y + offset + lift, left + image.width() + offset, y + height + offset + lift
            )
            if step < steps:
                self._later(ANIMATION_FRAME_MS, frame, step + 1)
            else:
                land()

        def land() -> None:
            self._table.delete(flyer, shadow)
            self._table.create_rectangle(
                end_x + SHADOW_OFFSET,
                end_y + SHADOW_OFFSET,
                end_x + width + SHADOW_OFFSET,
                end_y + height + SHADOW_OFFSET,
                fill=SHADOW_COLOR,
                outline="",
                tags=("round",),
            )
            self._cards[key].append(
                self._table.create_image(end_x, end_y, image=self._card_images.get(card), anchor=tk.NW, tags=("round",))
            )
            # Only count the card once it's on the table.
            hand = Hand()
            for dealt_card in dealt:
                hand.add_card(dealt_card)
            self._show_sum(key, hand)
            then()

        frame(0)

    def _show_sum(self, key: str, hand: Hand) -> None:
        """Update a hand's total with a quick gold flash, settling on red if it's bust."""
        item = self._sum_text[key]
        settle = BUST_COLOR if hand.is_bust() else TEXT_COLOR
        self._table.itemconfigure(item, text=f"Sum = {hand.total}")

        def fade(step: int) -> None:
            self._table.itemconfigure(item, fill=_blend(HIGHLIGHT_COLOR, settle, step / SUM_FLASH_FRAMES))
            if step < SUM_FLASH_FRAMES:
                self._later(SUM_FLASH_FRAME_MS, fade, step + 1)

        fade(0)

    # --- Turns -----------------------------------------------------------------------------

    def _after_player_card(self) -> None:
        assert self._round is not None
        if self._round.is_over:
            self._end_round()
        elif self._round.is_player_turn:
            self._set_buttons_enabled(True)
        else:
            self._player_reached_twenty_one()

    def _hit(self) -> None:
        assert self._round is not None
        self._set_buttons_enabled(False)
        self._round.hit()
        self._deal_new_cards(then=self._after_player_card)

    def _stand(self) -> None:
        assert self._round is not None
        self._round.stand()
        self._start_dealer_turn()

    def _player_reached_twenty_one(self) -> None:
        assert self._round is not None
        self._hide_controls()
        self._burst_confetti()
        # Only 21 on the first two cards is a blackjack.
        title = "Blackjack!" if self._round.is_blackjack else "21!"
        self._show_banner(
            title, "Dealer's turn...", "win", then=self._start_dealer_turn, hide_after_ms=BLACKJACK_BANNER_MS
        )

    def _start_dealer_turn(self) -> None:
        self._hide_controls()
        self._later(DEALER_TURN_DELAY_MS, self._dealer_step)

    def _dealer_step(self) -> None:
        assert self._round is not None
        # The dealer asks Jev over the network, so decide off the Tk thread to keep the window responsive.
        self._wait_for_dealer(_dealer_worker.submit(self._round.dealer_step))

    def _wait_for_dealer(self, decision: Future[Optional[Card]]) -> None:
        if not decision.done():
            self._later(DEALER_POLL_MS, self._wait_for_dealer, decision)
            return
        if decision.result() is None:
            self._end_round()
        else:
            self._deal_new_cards(then=lambda: self._later(DEALER_TURN_DELAY_MS, self._dealer_step))

    def _end_round(self) -> None:
        assert self._round is not None and self._round.outcome is not None
        outcome, bet = self._round.outcome, self._round.bet
        self._save.save(self.player)
        self._hide_controls()
        self._table.itemconfigure(self._bet_text, text="")
        self._refresh_status()
        out_of_chips = "  ·  Out of chips" if self._is_broke() else ""
        if outcome is Outcome.WIN:
            self._fire_confetti_cannons()
            self._open_betting(outcome.value, f"+{bet}$", "win")
        elif outcome is Outcome.LOSE:
            reason = "Bust! " if self.player.hand.is_bust() else ""
            self._open_betting(outcome.value, f"{reason}-{bet}${out_of_chips}", "lose")
        else:
            self._open_betting(outcome.value, f"Your {bet}$ bet is returned", "draw")

    # --- Banners and celebrations ----------------------------------------------------------

    def _show_banner(
        self,
        title: str,
        subtitle: str,
        style: str,
        then: Callable[[], None],
        hide_after_ms: Optional[int] = None,
    ) -> None:
        """Bring a banner in over the middle of the table, then call ``then``.

        Wins and draws pop in with a bounce; losses drop in from the top and shake.
        With ``hide_after_ms``, the banner clears itself before ``then`` is called.
        """
        fill, outline, title_color, subtitle_color = BANNER_STYLES[style]
        cx, cy = TABLE_WIDTH / 2, BANNER_Y
        panel = self._table.create_rectangle(0, 0, 0, 0, fill=fill, outline=outline, width=4, tags=("banner", "round"))
        title_item = self._table.create_text(cx, cy, text=title, fill=title_color, tags=("banner", "banner_title", "round"))
        subtitle_item = self._table.create_text(cx, cy, text=subtitle, fill=subtitle_color, tags=("banner", "round"))
        steps = max(1, BANNER_INTRO_MS // ANIMATION_FRAME_MS)
        drops_in = style == "lose"

        def place(scale: float, center_x: float, center_y: float) -> None:
            half_w, half_h = BANNER_WIDTH / 2 * scale, BANNER_HEIGHT / 2 * scale
            self._table.coords(panel, center_x - half_w, center_y - half_h, center_x + half_w, center_y + half_h)
            self._table.coords(title_item, center_x, center_y - 42 * scale)
            self._table.coords(subtitle_item, center_x, center_y + 6 * scale)
            self._table.itemconfigure(title_item, font=(BANNER_FONT[0], max(1, round(BANNER_FONT[1] * scale)), "bold"))
            self._table.itemconfigure(subtitle_item, font=(LABEL_FONT[0], max(1, round(20 * scale)), "bold"))

        def intro(step: int) -> None:
            t = step / steps
            if drops_in:
                # Fall from above the table, then shake as if it landed with a thud.
                fall = min(1.0, t / 0.6)
                shake = 0.0 if t < 0.6 else math.sin((t - 0.6) * 40) * 12 * (1 - t)
                place(1.0, cx + shake, -BANNER_HEIGHT + (cy + BANNER_HEIGHT) * _ease_out_cubic(fall))
            else:
                place(max(0.05, _ease_out_back(t)), cx, cy)
            if step < steps:
                self._later(ANIMATION_FRAME_MS, intro, step + 1)
            elif hide_after_ms is None:
                then()
            else:
                self._later(hide_after_ms, hide)

        def hide() -> None:
            self._table.delete("banner")
            then()

        self._table.tag_raise("banner")
        intro(0)

    def _fire_confetti_cannons(self) -> None:
        """Shoot confetti up and inwards from both bottom corners."""
        launches = []
        for side in (-1, 1):
            origin_x = 0 if side < 0 else TABLE_WIDTH
            for _ in range(CONFETTI_PER_BURST):
                speed, angle = random.uniform(11, 19), math.radians(random.uniform(55, 80))
                launches.append((origin_x, TABLE_HEIGHT, -side * speed * math.cos(angle), -speed * math.sin(angle)))
        self._animate_confetti(launches)

    def _burst_confetti(self) -> None:
        """A ring of confetti bursting out from the middle of the table."""
        launches = []
        for _ in range(CONFETTI_PER_BURST):
            speed, angle = random.uniform(4, 11), random.uniform(0, 2 * math.pi)
            launches.append((TABLE_WIDTH / 2, BANNER_Y, speed * math.cos(angle), speed * math.sin(angle) - 4))
        self._animate_confetti(launches)

    def _animate_confetti(self, launches: List[Tuple[float, float, float, float]]) -> None:
        """Each piece is a small rectangle that tumbles (spins and flips) as gravity pulls it down."""
        pieces = []
        for x, y, vx, vy in launches:
            item = self._table.create_polygon(
                0, 0, 0, 0, 0, 0, fill=random.choice(CONFETTI_COLORS), outline="", tags=("confetti", "round")
            )
            pieces.append([item, x, y, vx, vy, random.uniform(0, math.pi), random.uniform(-0.3, 0.3), random.uniform(4, 7)])
        steps = max(1, CONFETTI_MS // ANIMATION_FRAME_MS)

        def frame(step: int) -> None:
            for piece in pieces:
                item, x, y, vx, vy, angle, spin, size = piece
                vx, vy = vx * 0.985, vy * 0.985 + 0.45
                x, y, angle = x + vx, y + vy, angle + spin
                # Flipping end over end: the piece's apparent height swings between full and edge-on.
                half_w, half_h = size, size * 0.6 * abs(math.cos(angle * 1.7))
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                corners = []
                for dx, dy in ((-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)):
                    corners += [x + dx * cos_a - dy * sin_a, y + dx * sin_a + dy * cos_a]
                self._table.coords(item, *corners)
                piece[1:6] = [x, y, vx, vy, angle]
            # Keep the banner readable on top of the confetti.
            self._table.tag_raise("banner")
            if step < steps:
                self._later(ANIMATION_FRAME_MS, frame, step + 1)
            else:
                self._table.delete(*(piece[0] for piece in pieces))

        frame(0)


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
