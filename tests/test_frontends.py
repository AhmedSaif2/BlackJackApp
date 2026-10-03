import contextlib
import io
import tkinter as tk
import unittest
from unittest import mock

from blackjack import Action, Card, Dealer, Deck, Player, Suit, cli, gui
from blackjack.__main__ import main as entry_point
from tests import without_jev


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
    def run_cli(self, *answers: str) -> str:
        out = io.StringIO()
        self.prompts = []
        with contextlib.redirect_stdout(out):
            cli.main(ask=scripted(answers, self.prompts), delay=0)
        return out.getvalue()

    def test_quit_immediately(self):
        output = self.run_cli("Ann", "q")
        self.assertIn("Current Pocket Money = 2500$", output)
        self.assertIn("You leave with 2500$", output)

    def test_rejects_invalid_input_then_plays(self):
        # Empty name, a bad bet, a bad hit/stand answer, then a hit that busts.
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            output = self.run_cli("", "Ann", "7", "50", "x", "1", "q")
        self.assertIn("Please choose one of the listed bets.", output)
        self.assertIn("You Lost!", output)
        self.assertIn("You leave with 2450$", output)

    def test_out_of_money_ends_game(self):
        # Twelve busted 200$ bets leave 100$; once 200$ is unaffordable it is no longer offered.
        answers = ["Ann"] + ["200", "1"] * 12 + ["200", "50", "1", "50", "1"]
        decks = [stacked_deck("king", "queen", "2", "5") for _ in range(14)]
        with mock.patch("blackjack.game.Deck", side_effect=decks):
            output = self.run_cli(*answers)
        self.assertIn("Place a bet (10/50) or 'q' to quit: ", self.prompts)
        self.assertIn("You're out of money!", output)
        self.assertIn("You leave with 0$", output)

    def test_win_and_draw_payouts(self):
        decks = [
            stacked_deck("10", "9", "10", "7"),  # 19 vs 17
            stacked_deck("10", "8", "10", "8"),  # 18 vs 18
        ]
        with mock.patch("blackjack.game.Deck", side_effect=decks), dealer_hits_below_17():
            output = self.run_cli("Ann", "50", "2", "50", "2", "q")
        self.assertIn("You Won!", output)
        self.assertIn("Draw!", output)
        self.assertIn("You leave with 2550$", output)
        # The scoreboard after each round, then once more in the closing summary.
        self.assertEqual(output.count("Rounds: 1 | Wins: 1 | Losses: 0 | Draws: 0 | Win rate: 100%"), 1)
        self.assertEqual(output.count("Rounds: 2 | Wins: 1 | Losses: 0 | Draws: 1 | Win rate: 50%"), 2)
        self.assertIn("Blackjacks: 0 | Busts: 0 | Net: +50$ | Best: 2550$", output)
        self.assertIn("Scoreboard", output)

    def test_no_scoreboard_summary_without_rounds(self):
        output = self.run_cli("Ann", "q")
        self.assertNotIn("Scoreboard", output)

    def test_blackjack_on_deal(self):
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("ace", "king", "10", "10")):
            output = self.run_cli("Ann", "10", "q")
        self.assertIn("Blackjack!", output)
        self.assertIn("You Won!", output)


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
        try:
            self.app = gui.BlackjackApp()
        except tk.TclError as error:
            self.skipTest(f"No display available: {error}")
        self.app.withdraw()
        # Every banner shown (title, subtitle), and the page on screen when it appeared.
        self.messages = []
        self.subtitles = []
        self.pages_at_message = []
        show_banner = gui.GamePage._show_banner

        def record_banner(page, title, subtitle, *args, **kwargs):
            self.messages.append(title)
            self.subtitles.append(subtitle)
            self.pages_at_message.append(type(self.page()))
            return show_banner(page, title, subtitle, *args, **kwargs)

        # Run the round without waiting for the animations' full durations.
        for patcher in (
            mock.patch.object(gui.GamePage, "_show_banner", autospec=True, side_effect=record_banner),
            mock.patch.object(gui, "DEALER_TURN_DELAY_MS", 1),
            mock.patch.object(gui, "DEAL_ANIMATION_MS", 1),
            mock.patch.object(gui, "BANNER_INTRO_MS", 1),
            mock.patch.object(gui, "BLACKJACK_BANNER_MS", 1),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.app.destroy()

    def page(self):
        return self.app._page

    def click(self, text):
        (button,) = find(self.page(), tk.Button, text)
        self.assertEqual(str(button.cget("state")), tk.NORMAL)
        button.invoke()

    def labels(self):
        return [label.cget("text") for label in find(self.page(), tk.Label)]

    def sum_text(self, page, hand):
        return page._table.itemcget(page._sum_text[hand], "text")

    def wait_for(self, condition, timeout_ms=3000):
        for _ in range(timeout_ms // 10):
            self.app.update()
            if condition():
                return
            self.app.after(10)
        self.fail("Timed out waiting for the GUI")

    def buttons_enabled(self, page):
        return {str(button.cget("state")) for button in find(page, tk.Button)} == {tk.NORMAL}

    def continue_to_betting_page(self):
        """Wait for the result banner's Continue button and click it."""
        self.wait_for(lambda: find(self.page(), tk.Button, "Continue"))
        self.assertIsInstance(self.page(), gui.GamePage)
        self.click("Continue")
        self.assertIsInstance(self.page(), gui.BettingPage)

    def enter_name(self, name="Ann"):
        (entry,) = find(self.page(), tk.Entry)
        entry.insert(0, name)
        self.click("Play")

    def test_welcome_requires_name(self):
        self.assertNotIn("Please enter your name!", self.labels())
        self.click("Play")
        self.assertIn("Please enter your name!", self.labels())
        self.assertIsInstance(self.page(), gui.WelcomePage)

    def test_betting_page_shows_player(self):
        self.enter_name()
        self.assertIsInstance(self.page(), gui.BettingPage)
        self.assertIn("Welcome Ann", self.labels())
        self.assertIn("Pocket Money = 2500$", self.labels())
        self.assertNotIn("Scoreboard", self.labels())

    def test_bust_shows_loss_banner_then_returns_to_betting_page(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.click("50$")
            page = self.page()
            self.wait_for(lambda: self.buttons_enabled(page))
        self.assertEqual(self.sum_text(page, "player"), "Sum = 20")
        self.assertEqual(len(page._cards["player"]), 2)
        self.click("Hit")
        self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["You Lost!"])
        self.assertEqual(self.subtitles, ["Bust! -50$"])
        # No celebration for a loss, and the result stays on the table until the player moves on.
        self.assertEqual(page._table.find_withtag("confetti"), ())
        self.continue_to_betting_page()
        self.assertIn("Pocket Money = 2450$", self.labels())

    def test_win_celebrates_with_confetti(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "9", "10", "6", "king")), dealer_hits_below_17():
            self.click("200$")
            page = self.page()
            self.wait_for(lambda: self.buttons_enabled(page))
            self.click("Stand")
            hit, stand = find(page, tk.Button, "Hit")[0], find(page, tk.Button, "Stand")[0]
            self.assertEqual(str(hit.cget("state")), tk.DISABLED)
            self.assertEqual(str(stand.cget("state")), tk.DISABLED)
            self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["You Won!"])
        self.assertEqual(self.subtitles, ["+200$"])
        self.assertNotEqual(page._table.find_withtag("confetti"), ())
        # Hit and Stand are cleared away so the banner has the row to itself.
        self.assertEqual(page._table.itemcget(page._controls[0], "state"), tk.HIDDEN)
        self.continue_to_betting_page()
        self.assertIn("Pocket Money = 2700$", self.labels())

    def test_draw_returns_the_bet(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "8", "10", "8")), dealer_hits_below_17():
            self.click("50$")
            page = self.page()
            self.wait_for(lambda: self.buttons_enabled(page))
            self.click("Stand")
            self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["Draw!"])
        self.assertEqual(self.subtitles, ["Your 50$ bet is returned"])
        self.assertEqual(page._table.find_withtag("confetti"), ())
        self.continue_to_betting_page()
        self.assertIn("Pocket Money = 2500$", self.labels())

    def test_blackjack_on_deal_skips_to_dealer(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("ace", "king", "10", "10")):
            self.click("10$")
            self.wait_for(lambda: len(self.messages) == 2)
        self.assertEqual(self.messages, ["Blackjack!", "You Won!"])
        # The player's cards must be on the table when "Blackjack!" pops up.
        self.assertEqual(self.pages_at_message[0], gui.GamePage)
        self.continue_to_betting_page()
        self.assertIn("Pocket Money = 2510$", self.labels())

    def test_cards_fly_in_one_at_a_time(self):
        self.enter_name()
        with mock.patch.object(gui, "DEAL_ANIMATION_MS", 150), mock.patch(
            "blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")
        ):
            self.click("50$")
            page = self.page()
            hit, stand = find(page, tk.Button, "Hit")[0], find(page, tk.Button, "Stand")[0]

            # Mid-flight: one card (and its shadow) is moving, the hand's sum doesn't count it yet
            # and the buttons are locked.
            self.wait_for(lambda: page._table.find_withtag("flying"))
            self.assertEqual(len(page._table.find_withtag("flying")), 2)
            self.assertEqual(page._cards["player"], [])
            self.assertEqual(self.sum_text(page, "player"), "")
            self.assertEqual(str(hit.cget("state")), tk.DISABLED)
            self.assertEqual(str(stand.cget("state")), tk.DISABLED)

            # The sum follows the cards as they land.
            self.wait_for(lambda: self.sum_text(page, "player") == "Sum = 10")
            self.wait_for(lambda: self.sum_text(page, "player") == "Sum = 20")
            self.assertEqual(self.sum_text(page, "dealer"), "")
            self.wait_for(lambda: self.buttons_enabled(page))
            self.assertEqual(self.sum_text(page, "dealer"), "Sum = 2")
            self.assertEqual(page._table.find_withtag("flying"), ())

            # The hit is animated too, and the result waits until the card has landed.
            self.click("Hit")
            self.assertEqual(str(stand.cget("state")), tk.DISABLED)
            self.assertEqual(self.messages, [])
            self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["You Lost!"])
        self.assertEqual(len(page._cards["player"]), 3)

    def test_flip_frames_squeeze_the_card(self):
        images = gui.CardImages()
        card = Card("ace", Suit.SPADE)
        self.assertIs(images.squeezed(card, 72), images.get(card))
        edge_on = images.squeezed(None, 1)
        self.assertEqual((edge_on.width(), edge_on.height()), (2, 104))
        half = images.squeezed(card, 36)
        self.assertEqual((half.width(), half.height()), (36, 104))
        self.assertIs(images.squeezed(card, 37), half)

    def test_scoreboard_tracks_rounds_on_betting_page(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("ace", "king", "10", "10")):
            self.click("10$")
            self.continue_to_betting_page()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.click("50$")
            self.wait_for(lambda: self.buttons_enabled(self.page()))
            self.click("Hit")
            self.continue_to_betting_page()
        self.assertIn("Scoreboard", self.labels())
        self.assertIn("Rounds: 2 | Wins: 1 | Losses: 1 | Draws: 0 | Win rate: 50%", self.labels())
        self.assertIn("Blackjacks: 1 | Busts: 1 | Net: -40$ | Best: 2510$", self.labels())

    def test_scoreboard_shown_when_out_of_money(self):
        player = Player("Ann", 5)
        player.stats.record_loss(200, bust=True)
        self.app.show_betting_page(player)
        self.assertIn("You're out of money!", self.labels())
        self.assertIn("Scoreboard", self.labels())

    def test_unaffordable_bets_are_disabled_and_broke_player_can_restart(self):
        self.app.show_betting_page(Player("Ann", 60))
        states = {b.cget("text"): str(b.cget("state")) for b in find(self.page(), tk.Button)}
        self.assertEqual(states, {"10$": tk.NORMAL, "50$": tk.NORMAL, "200$": tk.DISABLED})

        self.app.show_betting_page(Player("Ann", 5))
        self.assertIn("You're out of money!", self.labels())
        self.click("Start over")
        self.assertIsInstance(self.page(), gui.WelcomePage)

    def test_every_card_image_loads(self):
        images = gui.CardImages()
        for card in Deck():
            image = images.get(card)
            self.assertEqual((image.width(), image.height()), (72, 104))


if __name__ == "__main__":
    unittest.main()
