import contextlib
import io
import re
import tkinter as tk
import unittest
from unittest import mock

from blackjack import Action, Card, Dealer, Deck, Player, Suit, cli, gui
from blackjack.game import new_player
from blackjack.__main__ import main as entry_point
from tests import temp_save, without_jev


_no_jev = without_jev()


def setUpModule():
    _no_jev.start()


def tearDownModule():
    _no_jev.stop()


class StackedDeck(Deck):
    """Deals the given ranks in order; Round's shuffle leaves it untouched."""

    def __init__(self, *ranks: str):
        super().__init__([Card(rank, Suit.HEART) for rank in reversed(ranks)])

    def shuffle(self) -> None:
        pass


stacked_deck = StackedDeck


def dealer_hits_below_17():
    return mock.patch.object(Dealer, "choose_action", new=lambda self, opponent_total=None: Action.HIT if self.hand.total < 17 else Action.STAND)


def scripted(answers, prompts):
    replies = iter(answers)

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return next(replies)

    return ask


class CliTests(unittest.TestCase):
    def setUp(self):
        self.save = temp_save(self)

    def run_cli(self, *answers: str) -> str:
        out = io.StringIO()
        self.prompts = []
        with contextlib.redirect_stdout(out):
            cli.main(ask=scripted(answers, self.prompts), delay=0, save=self.save)
        return out.getvalue()

    def test_starts_without_asking_for_a_name(self):
        output = self.run_cli("q")
        self.assertEqual(self.prompts, ["Bet 10/50/200, 'n' new game, 'q' quit: "])
        self.assertIn("Chips: 2500$", output)
        self.assertIn("You leave with 2500$", output)
        self.assertNotIn("Welcome back", output)

    def test_rejects_invalid_input_then_plays(self):
        # A bad bet, Enter with no previous bet, a bad hit/stand answer, then a hit that busts.
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            output = self.run_cli("7", "", "50", "x", "h", "q")
        self.assertEqual(output.count("Please choose one of the listed bets."), 2)
        self.assertIn("You Lost!", output)
        self.assertIn("You leave with 2450$", output)

    def test_enter_repeats_the_last_bet(self):
        decks = [stacked_deck("king", "queen", "2", "5") for _ in range(2)]
        with mock.patch("blackjack.game.Deck", side_effect=decks):
            output = self.run_cli("200", "h", "", "h", "q")
        self.assertIn("Bet 10/50/200, Enter for 200 again, 'n' new game, 'q' quit: ", self.prompts)
        self.assertIn("You leave with 2100$", output)

    def test_out_of_chips_offers_a_new_game(self):
        # Twelve busted 200$ bets leave 100$; once 200$ is unaffordable it's no longer offered or repeated.
        answers = ["200", "h"] * 12 + ["200", "50", "h", "50", "h", "x", "n", "q"]
        decks = [stacked_deck("king", "queen", "2", "5") for _ in range(14)]
        with mock.patch("blackjack.game.Deck", side_effect=decks):
            output = self.run_cli(*answers)
        self.assertIn("Bet 10/50, 'n' new game, 'q' quit: ", self.prompts)
        self.assertEqual(self.prompts.count("You're out of chips! Type 'n' to start over or 'q' to quit: "), 2)
        self.assertIn("New game! Your chips and stats have been reset.", output)
        self.assertIn("You leave with 2500$", output)
        self.assertEqual(self.save.load().stats, new_player().stats)

    def test_win_and_draw_payouts(self):
        decks = [
            stacked_deck("10", "9", "10", "7"),  # 19 vs 17
            stacked_deck("10", "8", "10", "8"),  # 18 vs 18
        ]
        with mock.patch("blackjack.game.Deck", side_effect=decks), dealer_hits_below_17():
            output = self.run_cli("50", "s", "50", "s", "q")
        self.assertIn("You Won!", output)
        self.assertIn("Draw!", output)
        self.assertIn("You leave with 2550$", output)
        # The scoreboard after each round, then once more in the closing summary.
        self.assertEqual(output.count("Rounds: 1 | Wins: 1 | Losses: 0 | Draws: 0 | Win rate: 100%"), 1)
        self.assertEqual(output.count("Rounds: 2 | Wins: 1 | Losses: 0 | Draws: 1 | Win rate: 50%"), 2)
        self.assertIn("Blackjacks: 0 | Busts: 0 | Net: +50$ | Best: 2550$", output)
        self.assertIn("Scoreboard", output)

    def test_no_scoreboard_summary_without_rounds(self):
        output = self.run_cli("q")
        self.assertNotIn("Scoreboard", output)

    def test_blackjack_on_deal(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("ace", "king", "10", "10")):
            output = self.run_cli("10", "q")
        self.assertIn("Blackjack!", output)
        self.assertIn("You Won!", output)

    def test_hitting_to_twenty_one_is_not_called_blackjack(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("5", "6", "10", "king", "7")), dealer_hits_below_17():
            output = self.run_cli("10", "h", "q")
        self.assertIn("21!", output)
        self.assertNotIn("Blackjack!", output)

    def test_progress_carries_over_to_the_next_session(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.run_cli("50", "h", "q")
        output = self.run_cli("q")
        self.assertIn("Welcome back!", output)
        self.assertIn("Chips: 2450$", output)

    def test_quitting_mid_hand_keeps_the_bet_lost(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "6", "10")), self.assertRaises(StopIteration):
            self.run_cli("200")  # the script runs out at the hit/stand prompt, like closing the console
        self.assertEqual(self.save.load().pocket_money, 2300)


class EntryPointTests(unittest.TestCase):
    def test_cli_flag_runs_console_game(self):
        with mock.patch("blackjack.cli.main") as cli_main, mock.patch("blackjack.gui.main") as gui_main:
            entry_point(["--cli"])
        cli_main.assert_called_once()
        gui_main.assert_not_called()

    def test_default_runs_gui(self):
        with mock.patch("blackjack.cli.main") as cli_main, mock.patch("blackjack.gui.main") as gui_main:
            entry_point([])
        gui_main.assert_called_once()
        cli_main.assert_not_called()

    def test_ctrl_c_exits_quietly(self):
        with mock.patch("blackjack.cli.main", side_effect=KeyboardInterrupt), contextlib.redirect_stdout(io.StringIO()):
            entry_point(["--cli"])


def find(widget: tk.Misc, cls, text=None):
    """All descendants of ``widget`` of type ``cls`` (optionally with the given text)."""
    found = []
    for child in widget.winfo_children():
        if isinstance(child, cls) and (text is None or child.cget("text") == text):
            found.append(child)
        found.extend(find(child, cls, text))
    return found


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.save = temp_save(self)
        # Every banner shown (title, subtitle), and how many of the player's cards were on the table then.
        self.messages = []
        self.subtitles = []
        self.player_cards_at_message = []
        show_banner = gui.Table._show_banner

        def record_banner(table, title, subtitle, *args, **kwargs):
            self.messages.append(title)
            self.subtitles.append(subtitle)
            self.player_cards_at_message.append(len(table._cards["player"]))
            return show_banner(table, title, subtitle, *args, **kwargs)

        # Run the round without waiting for the animations' full durations.
        for patcher in (
            mock.patch.object(gui.Table, "_show_banner", autospec=True, side_effect=record_banner),
            mock.patch.object(gui, "DEALER_TURN_DELAY_MS", 1),
            mock.patch.object(gui, "DEAL_ANIMATION_MS", 1),
            mock.patch.object(gui, "BANNER_INTRO_MS", 1),
            mock.patch.object(gui, "BLACKJACK_BANNER_MS", 1),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = None
        self.open_app()

    def open_app(self, player=None):
        """Start the app, as if ``player`` was what the last session saved, and wait for the bets."""
        if self.app is not None:
            self.close_app()
        if player is not None:
            self.save.save(player)
        try:
            self.app = gui.BlackjackApp(self.save)
        except tk.TclError as error:
            self.skipTest(f"No display available: {error}")
        self.app.withdraw()
        self.table = self.app.table
        self.wait_for(self.between_rounds)

    def close_app(self):
        # Cancel animation and dealer callbacks still pending, as closing the real window would.
        for pending in self.app.tk.splitlist(self.app.tk.call("after", "info")):
            self.app.tk.call("after", "cancel", pending)
        self.app.destroy()

    def tearDown(self):
        if self.app is not None:
            self.close_app()

    def click(self, text):
        (button,) = find(self.table, tk.Button, text)
        self.assertEqual(str(button.cget("state")), tk.NORMAL)
        button.invoke()

    def key(self, keysym):
        """Press a key. Windows won't give a withdrawn test window keyboard focus, so run its key binding directly."""
        script = self.app.bind(f"<KeyPress-{keysym}>")
        self.assertTrue(script, f"{keysym} is not bound")
        # Fill in the event fields Tk would substitute: the key, the window, and zero for the rest.
        fields = {"K": keysym, "A": keysym, "W": str(self.app), "T": "2"}
        self.app.tk.eval(re.sub(r"%(.)", lambda match: fields.get(match.group(1), "0"), script))

    def labels(self):
        return [label.cget("text") for label in find(self.table, tk.Label)]

    def chips(self):
        return self.table._chips_label.cget("text")

    def sum_text(self, hand):
        return self.table._table.itemcget(self.table._sum_text[hand], "text")

    def offered(self):
        """The row of buttons the banner is offering (bets or Start over), or None."""
        canvas = self.table._table
        for item in canvas.find_withtag("banner"):
            if canvas.type(item) == "window":
                return canvas.nametowidget(canvas.itemcget(item, "window"))
        return None

    def confetti(self):
        return self.table._table.find_withtag("confetti")

    def wait_for(self, condition, timeout_ms=3000):
        for _ in range(timeout_ms // 10):
            self.app.update()
            if condition():
                return
            self.app.after(10)
        self.fail("Timed out waiting for the GUI")

    def player_can_act(self):
        return str(self.table.hit_button.cget("state")) == tk.NORMAL

    def between_rounds(self):
        return self.offered() is not None

    def controls_hidden(self):
        canvas = self.table._table
        return {canvas.itemcget(control, "state") for control in self.table._controls} == {tk.HIDDEN}

    def play(self, bet, ranks, *moves):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck(*ranks)), dealer_hits_below_17():
            self.click(f"{bet}$")
            for move in moves:
                self.wait_for(self.player_can_act)
                self.click(move)
            self.wait_for(self.between_rounds)

    def test_opens_straight_on_the_table(self):
        self.assertIsInstance(self.table, gui.Table)
        self.assertEqual(find(self.table, tk.Entry), [])
        self.assertEqual((self.messages, self.subtitles), (["Blackjack"], ["Place your bet"]))
        self.assertIs(self.offered(), self.table._bet_row)
        states = {b.cget("text"): str(b.cget("state")) for b in self.table.bet_buttons.values()}
        self.assertEqual(states, {"10$": tk.NORMAL, "50$": tk.NORMAL, "200$": tk.NORMAL})
        self.assertEqual(self.chips(), "Chips: 2500$")
        self.assertIn("No hands played yet", self.labels())
        self.assertTrue(self.controls_hidden())

    def test_bust_shows_loss_banner_and_keeps_the_hand_on_the_table(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.click("50$")
            self.assertIsNone(self.offered())
            self.wait_for(self.player_can_act)
            self.assertEqual(self.sum_text("player"), "Sum = 20")
            self.assertEqual(len(self.table._cards["player"]), 2)
            self.click("Hit")
            self.wait_for(self.between_rounds)
        self.assertEqual((self.messages[-1], self.subtitles[-1]), ("You Lost!", "Bust! -50$"))
        # No celebration for a loss, and the losing hand stays in view under the bets.
        self.assertEqual(self.confetti(), ())
        self.assertEqual(len(self.table._cards["player"]), 3)
        self.assertEqual(self.chips(), "Chips: 2450$")

    def test_win_celebrates_with_confetti(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "9", "10", "6", "king")), dealer_hits_below_17():
            self.click("200$")
            self.wait_for(self.player_can_act)
            self.click("Stand")
            self.assertFalse(self.player_can_act())
            self.assertEqual(str(self.table.stand_button.cget("state")), tk.DISABLED)
            self.assertEqual(str(self.table.new_game_button.cget("state")), tk.DISABLED)
            self.wait_for(self.between_rounds)
        self.assertEqual((self.messages[-1], self.subtitles[-1]), ("You Won!", "+200$"))
        self.assertNotEqual(self.confetti(), ())
        # Hit and Stand are cleared away so the banner has the row to itself.
        self.assertTrue(self.controls_hidden())
        self.assertEqual(self.chips(), "Chips: 2700$")
        self.assertEqual(str(self.table.new_game_button.cget("state")), tk.NORMAL)

    def test_draw_returns_the_bet(self):
        self.play(50, ("10", "8", "10", "8"), "Stand")
        self.assertEqual((self.messages[-1], self.subtitles[-1]), ("Draw!", "Your 50$ bet is returned"))
        self.assertEqual(self.confetti(), ())
        self.assertEqual(self.chips(), "Chips: 2500$")

    def test_blackjack_on_deal_skips_to_dealer(self):
        self.play(10, ("ace", "king", "10", "10"))
        self.assertEqual(self.messages[1:], ["Blackjack!", "You Won!"])
        # The player's cards must be on the table when "Blackjack!" pops up.
        self.assertEqual(self.player_cards_at_message[1], 2)
        self.assertEqual(self.chips(), "Chips: 2510$")

    def test_hitting_to_twenty_one_is_not_called_blackjack(self):
        self.play(10, ("5", "6", "10", "king", "7"), "Hit")
        self.assertEqual(self.messages[1:], ["21!", "You Won!"])

    def test_next_bet_clears_the_table(self):
        self.play(50, ("king", "queen", "2", "5"), "Hit")
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "6", "3")):
            self.click("10$")
            self.assertEqual(self.table._table.find_withtag("banner"), ())
            self.assertEqual(self.table._cards, {"dealer": [], "player": []})
            self.assertEqual(self.sum_text("player"), "")
            self.wait_for(self.player_can_act)
        self.assertEqual(len(self.table._cards["player"]), 2)
        self.assertEqual(len(self.table._cards["dealer"]), 1)

    def test_betting_again_mid_confetti_sweeps_it_away(self):
        self.play(50, ("10", "9", "10", "7"), "Stand")
        self.assertNotEqual(self.confetti(), ())
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "6", "3")):
            self.key("Return")
            self.assertEqual(self.confetti(), ())
            self.wait_for(self.player_can_act)
        self.assertEqual(self.confetti(), ())

    def test_keyboard_shortcuts(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.key("h")  # nothing to hit yet
            self.key("Return")  # no previous bet to repeat
            self.assertIs(self.offered(), self.table._bet_row)
            self.key("2")
            self.assertIsNone(self.offered())
            self.assertEqual(self.chips(), "Chips: 2450$")
            self.key("3")  # betting is closed during a hand
            self.assertEqual(self.chips(), "Chips: 2450$")
            self.wait_for(self.player_can_act)
            self.key("H")
            self.wait_for(self.between_rounds)
        self.assertEqual(self.subtitles[-1], "Bust! -50$")
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "9", "10", "7")), dealer_hits_below_17():
            self.key("Return")  # same bet again
            self.assertEqual(self.chips(), "Chips: 2400$")
            self.wait_for(self.player_can_act)
            self.key("s")
            self.wait_for(self.between_rounds)
        self.assertEqual(self.chips(), "Chips: 2500$")

    def test_scoreboard_tracks_rounds(self):
        self.play(10, ("ace", "king", "10", "10"))
        self.play(50, ("king", "queen", "2", "5"), "Hit")
        self.assertIn("Rounds: 2 | Wins: 1 | Losses: 1 | Draws: 0 | Win rate: 50%", self.labels())
        self.assertIn("Blackjacks: 1 | Busts: 1 | Net: -40$ | Best: 2510$", self.labels())

    def test_progress_is_saved_and_restored(self):
        self.play(50, ("king", "queen", "2", "5"), "Hit")
        self.open_app()
        self.assertEqual(self.messages[-1], "Welcome back!")
        self.assertEqual(self.chips(), "Chips: 2450$")
        self.assertIn("Rounds: 1 | Wins: 0 | Losses: 1 | Draws: 0 | Win rate: 0%", self.labels())

    def test_bet_is_saved_as_soon_as_it_is_placed(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "6", "3")):
            self.click("200$")
        self.assertEqual(self.save.load().pocket_money, 2300)

    def test_unaffordable_bets_are_disabled(self):
        self.open_app(Player("You", 60))
        states = {b.cget("text"): str(b.cget("state")) for b in self.table.bet_buttons.values()}
        self.assertEqual(states, {"10$": tk.NORMAL, "50$": tk.NORMAL, "200$": tk.DISABLED})
        self.key("3")
        self.assertEqual(self.chips(), "Chips: 60$")

    def test_out_of_chips_can_start_over(self):
        broke = Player("You", 5)
        broke.stats.record_loss(200, bust=True)
        self.open_app(broke)
        self.assertEqual(self.messages[-1], "Out of chips")
        self.assertIs(self.offered(), self.table._start_over_row)
        self.assertIn("Rounds: 1 | Wins: 0 | Losses: 1 | Draws: 0 | Win rate: 0%", self.labels())
        self.click("Start over")
        self.wait_for(self.between_rounds)
        self.assertEqual(self.messages[-1], "New game")
        self.assertIs(self.offered(), self.table._bet_row)
        self.assertEqual(self.chips(), "Chips: 2500$")
        self.assertIn("No hands played yet", self.labels())
        self.assertEqual(self.save.load().pocket_money, 2500)

    def test_losing_the_last_chips_offers_start_over(self):
        self.open_app(Player("You", 10))
        self.play(10, ("king", "queen", "2", "5"), "Hit")
        self.assertEqual(self.subtitles[-1], "Bust! -10$  ·  Out of chips")
        self.assertIs(self.offered(), self.table._start_over_row)

    def test_new_game_asks_first(self):
        self.play(50, ("king", "queen", "2", "5"), "Hit")
        with mock.patch.object(gui.messagebox, "askyesno", return_value=False) as ask:
            self.table.new_game_button.invoke()
        ask.assert_called_once()
        self.assertEqual(self.chips(), "Chips: 2450$")
        with mock.patch.object(gui.messagebox, "askyesno", return_value=True):
            self.table.new_game_button.invoke()
        self.wait_for(self.between_rounds)
        self.assertEqual(self.chips(), "Chips: 2500$")
        self.assertEqual(self.table._cards, {"dealer": [], "player": []})
        self.assertEqual(self.save.load().stats, new_player().stats)

    def test_cards_fly_in_one_at_a_time(self):
        table, canvas = self.table, self.table._table
        with mock.patch.object(gui, "DEAL_ANIMATION_MS", 150), mock.patch(
            "blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")
        ):
            self.click("50$")

            # Mid-flight: one card (and its shadow) is moving, the hand's sum doesn't count it yet
            # and the buttons are locked.
            self.wait_for(lambda: canvas.find_withtag("flying"))
            self.assertEqual(len(canvas.find_withtag("flying")), 2)
            self.assertEqual(table._cards["player"], [])
            self.assertEqual(self.sum_text("player"), "")
            self.assertFalse(self.player_can_act())

            # The sum follows the cards as they land.
            self.wait_for(lambda: self.sum_text("player") == "Sum = 10")
            self.wait_for(lambda: self.sum_text("player") == "Sum = 20")
            self.assertEqual(self.sum_text("dealer"), "")
            self.wait_for(self.player_can_act)
            self.assertEqual(self.sum_text("dealer"), "Sum = 2")
            self.assertEqual(canvas.find_withtag("flying"), ())

            # The hit is animated too, and the result waits until the card has landed.
            banners_before = len(self.messages)
            self.click("Hit")
            self.assertFalse(self.player_can_act())
            self.assertEqual(len(self.messages), banners_before)
            self.wait_for(self.between_rounds)
        self.assertEqual(self.messages[-1], "You Lost!")
        self.assertEqual(len(table._cards["player"]), 3)

    def test_flip_frames_squeeze_the_card(self):
        images = gui.CardImages()
        card = Card("ace", Suit.SPADE)
        self.assertIs(images.squeezed(card, 72), images.get(card))
        edge_on = images.squeezed(None, 1)
        self.assertEqual((edge_on.width(), edge_on.height()), (2, 104))
        half = images.squeezed(card, 36)
        self.assertEqual((half.width(), half.height()), (36, 104))
        self.assertIs(images.squeezed(card, 37), half)

    def test_every_card_image_loads(self):
        images = gui.CardImages()
        for card in Deck():
            image = images.get(card)
            self.assertEqual((image.width(), image.height()), (72, 104))


if __name__ == "__main__":
    unittest.main()
