import contextlib
import io
import tkinter as tk
import unittest
from unittest import mock

from blackjack import Action, Card, Dealer, Deck, Player, Suit, cli, gui
from blackjack.__main__ import main as entry_point


class StackedDeck(Deck):
    """Deals the given ranks in order; Round's shuffle leaves it untouched."""

    def __init__(self, *ranks: str):
        super().__init__([Card(rank, Suit.HEART) for rank in reversed(ranks)])

    def shuffle(self) -> None:
        pass


stacked_deck = StackedDeck


def dealer_hits_below_17():
    return mock.patch.object(Dealer, "choose_action", new=lambda self: Action.HIT if self.hand.total < 17 else Action.STAND)


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
        self.messages = []
        # The page on screen when each message box appeared.
        self.pages_at_message = []
        patcher = mock.patch.object(gui.messagebox, "showinfo", side_effect=self.record_message)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Run the dealer's turn without waiting a second per card.
        delay = mock.patch.object(gui, "DEALER_TURN_DELAY_MS", 1)
        delay.start()
        self.addCleanup(delay.stop)
        # Likewise, deal cards without the slide-in animation's full duration.
        animation = mock.patch.object(gui, "DEAL_ANIMATION_MS", 1)
        animation.start()
        self.addCleanup(animation.stop)

    def tearDown(self):
        self.app.destroy()

    def record_message(self, _title, message):
        self.messages.append(message)
        self.pages_at_message.append(type(self.page()))

    def page(self):
        return self.app._page

    def click(self, text):
        (button,) = find(self.page(), tk.Button, text)
        self.assertEqual(str(button.cget("state")), tk.NORMAL)
        button.invoke()

    def labels(self):
        return [label.cget("text") for label in find(self.page(), tk.Label)]

    def wait_for(self, condition, timeout_ms=3000):
        for _ in range(timeout_ms // 10):
            self.app.update()
            if condition():
                return
            self.app.after(10)
        self.fail("Timed out waiting for the GUI")

    def buttons_enabled(self, page):
        return {str(button.cget("state")) for button in find(page, tk.Button)} == {tk.NORMAL}

    def enter_name(self, name="Ann"):
        (entry,) = find(self.page(), tk.Entry)
        entry.insert(0, name)
        self.click("Play")

    def test_welcome_requires_name(self):
        self.click("Play")
        self.assertEqual(self.messages, ["Please enter your name!"])
        self.assertIsInstance(self.page(), gui.WelcomePage)

    def test_betting_page_shows_player(self):
        self.enter_name()
        self.assertIsInstance(self.page(), gui.BettingPage)
        self.assertIn("Welcome Ann", self.labels())
        self.assertIn("Pocket Money = 2500$", self.labels())
        self.assertNotIn("Scoreboard", self.labels())

    def test_bust_returns_to_betting_page(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.click("50$")
            self.wait_for(lambda: self.buttons_enabled(self.page()))
        self.assertIsInstance(self.page(), gui.GamePage)
        self.assertIn("Sum = 20", self.labels())
        self.assertEqual(len(find(self.page()._player_cards, tk.Label)), 2)
        self.click("Hit")
        self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["You Lost!"])
        self.assertIsInstance(self.page(), gui.BettingPage)
        self.assertIn("Pocket Money = 2450$", self.labels())

    def test_stand_plays_dealer_turn_and_pays_out(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("10", "9", "10", "6", "king")), dealer_hits_below_17():
            self.click("200$")
            game_page = self.page()
            self.wait_for(lambda: self.buttons_enabled(game_page))
            self.click("Stand")
            hit, stand = find(game_page, tk.Button, "Hit")[0], find(game_page, tk.Button, "Stand")[0]
            self.assertEqual(str(hit.cget("state")), tk.DISABLED)
            self.assertEqual(str(stand.cget("state")), tk.DISABLED)
            self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["You Won!"])
        self.assertIsInstance(self.page(), gui.BettingPage)
        self.assertIn("Pocket Money = 2700$", self.labels())

    def test_blackjack_on_deal_skips_to_dealer(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("ace", "king", "10", "10")):
            self.click("10$")
            self.wait_for(lambda: len(self.messages) == 2)
        self.assertEqual(self.messages, ["Blackjack!", "You Won!"])
        # The player's cards must be on screen when "Blackjack!" pops up.
        self.assertEqual(self.pages_at_message[0], gui.GamePage)
        self.assertIn("Pocket Money = 2510$", self.labels())

    def test_cards_slide_in_one_at_a_time(self):
        self.enter_name()
        with mock.patch.object(gui, "DEAL_ANIMATION_MS", 150), mock.patch(
            "blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")
        ):
            self.click("50$")
            page = self.page()
            player_cards, player_sum = page._player_cards, page._player_sum
            hit, stand = find(page, tk.Button, "Hit")[0], find(page, tk.Button, "Stand")[0]

            # Mid-flight: one card is moving, the hand's sum doesn't count it yet and the buttons are locked.
            self.wait_for(lambda: len(find(player_cards, tk.Label)) == 1)
            flyers = [w for w in page.winfo_children() if isinstance(w, tk.Label) and w.winfo_manager() == "place"]
            self.assertEqual(len(flyers), 2)  # the deck and the card in flight
            self.assertEqual(player_sum.cget("text"), "")
            self.assertEqual(str(hit.cget("state")), tk.DISABLED)
            self.assertEqual(str(stand.cget("state")), tk.DISABLED)

            # The sum follows the cards as they land.
            self.wait_for(lambda: player_sum.cget("text") == "Sum = 10")
            self.wait_for(lambda: player_sum.cget("text") == "Sum = 20")
            self.assertEqual(page._dealer_sum.cget("text"), "")
            self.wait_for(lambda: self.buttons_enabled(page))
            self.assertEqual(page._dealer_sum.cget("text"), "Sum = 2")

            # Only the deck is left placed on the table, and the hit is animated too.
            placed = [w for w in page.winfo_children() if w.winfo_manager() == "place"]
            self.assertEqual(placed, [page._deck])
            self.click("Hit")
            self.assertEqual(str(stand.cget("state")), tk.DISABLED)
            self.assertEqual(self.messages, [])
            self.wait_for(lambda: self.messages)
        self.assertEqual(self.messages, ["You Lost!"])

    def test_scoreboard_tracks_rounds_on_betting_page(self):
        self.enter_name()
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("ace", "king", "10", "10")):
            self.click("10$")
            self.wait_for(lambda: isinstance(self.page(), gui.BettingPage))
        with mock.patch("blackjack.game.Deck", return_value=stacked_deck("king", "queen", "2", "5")):
            self.click("50$")
            self.wait_for(lambda: self.buttons_enabled(self.page()))
            self.click("Hit")
            self.wait_for(lambda: isinstance(self.page(), gui.BettingPage))
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
