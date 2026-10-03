"""Tkinter front-end: welcome page -> betting page -> game page."""

from __future__ import annotations

import math
import random
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from .cards import Card, Suit
from .game import BET_OPTIONS, STARTING_POCKET_MONEY, Outcome, Round
from .hand import Hand
from .participants import Dealer, Participant, Player

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

# Table layout (canvas coordinates; cards are 72x104).
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
# Result banners cover the controls row, leaving both hands in view.
BANNER_Y = 425
BANNER_WIDTH, BANNER_HEIGHT = 440, 150

TABLE_GREEN = "#2e8b57"  # SeaGreen, as in the original WinForms app
SHADOW_COLOR = "#1d5e3a"
TEXT_COLOR = "#ffffff"
HIGHLIGHT_COLOR = "#ffd54f"
BUST_COLOR = "#ff8a80"
ERROR_COLOR = "#ffd54f"
CARD_BACK_COLOR = "#1f3c88"
CARD_BACK_ALT = "#2c55b0"
CARD_BACK_TRIM = "#8fb0f0"
TITLE_FONT = ("Segoe UI", 36)
LABEL_FONT = ("Segoe UI", 20)
BUTTON_FONT = ("Segoe UI", 15)
SCOREBOARD_FONT = ("Segoe UI", 12)
BANNER_FONT = ("Segoe UI", 38)
# Mid-flip card frames are made in steps of this many pixels wide.
SQUEEZE_STEP = 6
MAX_SQUEEZED_IMAGES = 150


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
        # Shown under the name box instead of a pop-up when the name is missing.
        self._error = _label(self, "", BUTTON_FONT)
        self._error.config(fg=ERROR_COLOR)
        self._error.pack(pady=(14, 0))
        _button(self, "Play", self._play).pack(pady=(14, 50))

    def _play(self) -> None:
        name = self._name.get().strip()
        if not name:
            self._error.config(text="Please enter your name!")
            self._name.focus_set()
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


# One background thread runs the dealer's decisions, one at a time.
_dealer_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dealer")

# Banner looks: (panel fill, panel outline, title colour, subtitle colour).
BANNER_STYLES = {
    "win": ("#f5c518", "#fff3b0", "#3b2a00", "#5c4300"),
    "lose": ("#8b1e2d", "#d9727f", "white", "#f3c9cf"),
    "draw": ("#37474f", "#90a4ae", "white", "#cfd8dc"),
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


class GamePage(tk.Frame):
    """The table, drawn on a canvas so cards can fly, flip and be celebrated over."""

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
        self._bet = bet
        self._card_images = card_images
        self._on_round_over = on_round_over
        # Animation callbacks still waiting to run; cancelled if the page closes first.
        self._pending: Set[str] = set()

        # A fixed-size table, kept centred if the window is made bigger.
        self._table = tk.Canvas(self, width=TABLE_WIDTH, height=TABLE_HEIGHT, bg=TABLE_GREEN, highlightthickness=0)
        self._table.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        right = TABLE_WIDTH - TABLE_MARGIN_X
        self._sum_text: Dict[str, int] = {}
        for key, title, title_y in (("dealer", "Dealer Cards", DEALER_TITLE_Y), ("player", "Your Cards", PLAYER_TITLE_Y)):
            self._table.create_text(TABLE_MARGIN_X, title_y, text=title, font=LABEL_FONT, fill=TEXT_COLOR, anchor=tk.W)
            self._sum_text[key] = self._table.create_text(right, title_y, text="", font=LABEL_FONT, fill=TEXT_COLOR, anchor=tk.E)
        self._table.create_text(BET_X, CONTROLS_Y, text=f"Bet = {bet}$", font=LABEL_FONT, fill=TEXT_COLOR)

        self._hit_button = _button(self._table, "Hit", self._hit)
        self._stand_button = _button(self._table, "Stand", self._stand)
        self._controls = [
            self._table.create_window(TABLE_MARGIN_X + 25, CONTROLS_Y, window=self._hit_button, anchor=tk.W),
            self._table.create_window(TABLE_MARGIN_X + 145, CONTROLS_Y, window=self._stand_button, anchor=tk.W),
        ]

        # The deck: a few backs stacked with a slight offset, so it reads as a pile.
        for depth in range(DECK_DEPTH, 0, -1):
            self._table.create_image(DECK_X + depth * 2, DECK_Y + depth * 2, image=card_images.back(), anchor=tk.NW)
        self._table.create_image(DECK_X, DECK_Y, image=card_images.back(), anchor=tk.NW)

        self._round = Round(player, Dealer(), bet)
        # Canvas items of the cards that have landed in each hand.
        self._cards: Dict[str, List[int]] = {"dealer": [], "player": []}
        self._set_buttons_enabled(False)
        # Wait until the page is on screen, so the first card is seen leaving the deck.
        self._later(0, self._deal_new_cards, self._after_player_card)

    def _later(self, ms: int, callback: Callable[..., None], *args) -> None:
        """``after``, cancelled if the page is closed first (say, Continue mid-confetti)."""

        def run() -> None:
            self._pending.discard(after_id)
            callback(*args)

        after_id = self.after(ms, run)
        self._pending.add(after_id)

    def destroy(self) -> None:
        for after_id in self._pending:
            self.after_cancel(after_id)
        self._pending.clear()
        super().destroy()

    def _hide_controls(self) -> None:
        """Once the player's turn is over, clear the buttons away to make room for banners."""
        self._set_buttons_enabled(False)
        for control in self._controls:
            self._table.itemconfigure(control, state=tk.HIDDEN)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self._hit_button.config(state=state)
        self._stand_button.config(state=state)

    # --- Dealing ---------------------------------------------------------------------------

    def _deal_new_cards(self, then: Callable[[], None]) -> None:
        """Animate each card that isn't on the table yet, one at a time, then call ``then``.

        The player's cards go first, the same order ``Round`` deals the opening hand in.
        """
        for key, participant in (("player", self._player), ("dealer", self._round.dealer)):
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
        shadow = self._table.create_rectangle(0, 0, 0, 0, fill=SHADOW_COLOR, outline="", tags=("flying",))
        flyer = self._table.create_image(DECK_X, DECK_Y, image=self._card_images.back(), anchor=tk.NW, tags=("flying",))
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
            )
            self._cards[key].append(self._table.create_image(end_x, end_y, image=self._card_images.get(card), anchor=tk.NW))
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
        self._hide_controls()
        self._burst_confetti()
        self._show_banner(
            "Blackjack!", "Dealer's turn...", "win", then=self._start_dealer_turn, hide_after_ms=BLACKJACK_BANNER_MS
        )

    def _start_dealer_turn(self) -> None:
        self._hide_controls()
        self._later(DEALER_TURN_DELAY_MS, self._dealer_step)

    def _dealer_step(self) -> None:
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
        outcome: Optional[Outcome] = self._round.outcome
        assert outcome is not None
        self._hide_controls()
        if outcome is Outcome.WIN:
            self._fire_confetti_cannons()
            self._show_banner(outcome.value, f"+{self._bet}$", "win", then=self._show_continue_button)
        elif outcome is Outcome.LOSE:
            reason = "Bust! " if self._player.hand.is_bust() else ""
            self._show_banner(outcome.value, f"{reason}-{self._bet}$", "lose", then=self._show_continue_button)
        else:
            self._show_banner(outcome.value, f"Your {self._bet}$ bet is returned", "draw", then=self._show_continue_button)

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
        panel = self._table.create_rectangle(0, 0, 0, 0, fill=fill, outline=outline, width=4, tags=("banner",))
        title_item = self._table.create_text(cx, cy, text=title, fill=title_color, tags=("banner", "banner_title"))
        subtitle_item = self._table.create_text(cx, cy, text=subtitle, fill=subtitle_color, tags=("banner",))
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

    def _show_continue_button(self) -> None:
        button = _button(self._table, "Continue", lambda: self._on_round_over(self._player))
        button.bind("<Return>", lambda _event: button.invoke())
        self._table.create_window(TABLE_WIDTH / 2, BANNER_Y + 48, window=button, tags=("banner",))
        button.focus_set()

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
                0, 0, 0, 0, 0, 0, fill=random.choice(CONFETTI_COLORS), outline="", tags=("confetti",)
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
