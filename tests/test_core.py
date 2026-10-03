import random
import unittest

from blackjack import Action, Card, Dealer, Deck, Hand, Outcome, Player, PlayerStats, Round, Suit


def stacked_deck(*ranks: str) -> Deck:
    """A deck that deals ``ranks`` in the given order (drawing pops from the end)."""
    return Deck([Card(rank, Suit.SPADE) for rank in reversed(ranks)])


class FixedDealer(Dealer):
    """A dealer that hits below ``stand_at`` and stands otherwise, without randomness."""

    def __init__(self, stand_at: int = 17):
        super().__init__()
        self.stand_at = stand_at

    def choose_action(self) -> Action:
        return Action.HIT if self.hand.total < self.stand_at else Action.STAND


class CardTests(unittest.TestCase):
    def test_values(self):
        self.assertEqual(Card("2", Suit.HEART).value, 2)
        self.assertEqual(Card("10", Suit.HEART).value, 10)
        for face in ("jack", "queen", "king"):
            self.assertEqual(Card(face, Suit.CLUB).value, 10)
        self.assertEqual(Card("ace", Suit.SPADE).value, 11)

    def test_invalid_rank(self):
        with self.assertRaises(ValueError):
            Card("1", Suit.HEART)

    def test_image_name_matches_asset_naming(self):
        self.assertEqual(Card("ace", Suit.SPADE).image_name, "ace_of_spades")
        self.assertEqual(Card("10", Suit.DIAMOND).image_name, "10_of_diamonds")

    def test_str_is_readable(self):
        self.assertEqual(str(Card("queen", Suit.CLUB)), "Queen of Clubs")
        self.assertEqual(str(Card("7", Suit.HEART)), "7 of Hearts")


class DeckTests(unittest.TestCase):
    def test_full_deck_is_52_unique_cards(self):
        deck = Deck()
        self.assertEqual(len(deck), 52)
        self.assertEqual(len(set(deck)), 52)

    def test_shuffle_keeps_cards(self):
        deck = Deck(rng=random.Random(1))
        before = sorted(card.image_name for card in deck)
        deck.shuffle()
        self.assertEqual(sorted(card.image_name for card in deck), before)

    def test_draw_removes_card(self):
        deck = Deck()
        card = deck.draw()
        self.assertEqual(len(deck), 51)
        self.assertNotIn(card, list(deck))

    def test_draw_from_empty_deck(self):
        with self.assertRaises(IndexError):
            Deck([]).draw()


class HandTests(unittest.TestCase):
    def hand(self, *ranks):
        hand = Hand()
        for rank in ranks:
            hand.add_card(Card(rank, Suit.HEART))
        return hand

    def test_ace_flexibility(self):
        self.assertEqual(self.hand("ace", "king").total, 21)
        self.assertEqual(self.hand("ace", "ace").total, 12)
        self.assertEqual(self.hand("ace", "5", "king").total, 16)
        self.assertEqual(self.hand("ace", "ace", "9").total, 21)
        self.assertEqual(self.hand("ace", "ace", "ace", "ace").total, 14)

    def test_twenty_one_and_bust(self):
        self.assertTrue(self.hand("7", "7", "7").is_twenty_one())
        self.assertTrue(self.hand("king", "queen", "2").is_bust())
        self.assertFalse(self.hand("king", "ace").is_bust())


class ParticipantTests(unittest.TestCase):
    def test_place_bet(self):
        player = Player("Ann", 100)
        self.assertTrue(player.place_bet(60))
        self.assertEqual(player.pocket_money, 40)
        self.assertFalse(player.place_bet(50))
        self.assertFalse(player.place_bet(0))
        self.assertEqual(player.pocket_money, 40)

    def test_dealer_policy(self):
        dealer = Dealer(rng=random.Random(0))
        for ranks, expected in ((("10", "4"), Action.HIT), (("10", "9"), Action.STAND)):
            dealer.reset_hand()
            for rank in ranks:
                dealer.add_card(Card(rank, Suit.CLUB))
            self.assertIs(dealer.choose_action(), expected)

        # Between 15 and 18 the dealer flips a coin; both choices should show up.
        dealer.reset_hand()
        dealer.add_card(Card("10", Suit.CLUB))
        dealer.add_card(Card("6", Suit.CLUB))
        self.assertEqual({dealer.choose_action() for _ in range(50)}, {Action.HIT, Action.STAND})

    def test_deal_card(self):
        deck, player = Deck(), Player("Ann", 10)
        card = Dealer().deal_card(deck, player)
        self.assertEqual(player.hand.cards, [card])
        self.assertEqual(len(deck), 51)


class RoundTests(unittest.TestCase):
    def setUp(self):
        self.player = Player("Ann", 1000)
        self.dealer = FixedDealer()

    def test_initial_deal_and_bet(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("2", "3", "4"))
        self.assertEqual(self.player.pocket_money, 950)
        self.assertEqual(len(self.player.hand), 2)
        self.assertEqual(len(self.dealer.hand), 1)
        self.assertTrue(game.is_player_turn)

    def test_cannot_bet_more_than_pocket_money(self):
        with self.assertRaises(ValueError):
            Round(self.player, self.dealer, 5000)
        self.assertEqual(self.player.pocket_money, 1000)

    def test_player_bust_loses_bet(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("king", "queen", "5", "2"))
        game.hit()
        self.assertIs(game.outcome, Outcome.LOSE)
        self.assertFalse(game.is_player_turn)
        self.assertEqual(self.player.pocket_money, 950)
        self.assertIsNone(game.dealer_step())

    def test_player_wins_when_dealer_busts(self):
        # Player 10+8=18 stands; dealer 10, then 6 (16 -> hit), then king (bust).
        game = Round(self.player, self.dealer, 50, stacked_deck("10", "8", "10", "6", "king"))
        game.stand()
        self.assertEqual(len(game.play_dealer()), 2)
        self.assertTrue(self.dealer.hand.is_bust())
        self.assertIs(game.outcome, Outcome.WIN)
        self.assertEqual(self.player.pocket_money, 1050)

    def test_higher_total_wins(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("10", "9", "10", "7"))
        game.stand()
        game.play_dealer()
        self.assertIs(game.outcome, Outcome.WIN)
        self.assertEqual(self.player.pocket_money, 1050)

    def test_draw_returns_bet(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("10", "8", "10", "8"))
        game.stand()
        game.play_dealer()
        self.assertIs(game.outcome, Outcome.DRAW)
        self.assertEqual(self.player.pocket_money, 1000)

    def test_dealer_higher_total_wins(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("10", "7", "10", "9"))
        game.stand()
        game.play_dealer()
        self.assertIs(game.outcome, Outcome.LOSE)
        self.assertEqual(self.player.pocket_money, 950)

    def test_twenty_one_on_deal_ends_player_turn(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("ace", "king", "10", "10"))
        self.assertTrue(self.player.hand.is_twenty_one())
        self.assertFalse(game.is_player_turn)
        with self.assertRaises(RuntimeError):
            game.hit()
        game.play_dealer()
        self.assertIs(game.outcome, Outcome.WIN)

    def test_hitting_to_twenty_one_ends_player_turn(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("5", "6", "10", "king"))
        game.hit()
        self.assertTrue(self.player.hand.is_twenty_one())
        self.assertFalse(game.is_player_turn)

    def test_dealer_cannot_play_before_player_finishes(self):
        game = Round(self.player, self.dealer, 50, stacked_deck("2", "3", "4"))
        with self.assertRaises(RuntimeError):
            game.dealer_step()

    def test_dealer_stops_at_twenty_one(self):
        # Even a dealer that would always hit stops once it reaches 21.
        dealer = FixedDealer(stand_at=99)
        game = Round(self.player, dealer, 50, stacked_deck("10", "9", "10", "ace", "5"))
        game.stand()
        game.play_dealer()
        self.assertEqual(dealer.hand.total, 21)
        self.assertIs(game.outcome, Outcome.LOSE)

    def test_random_rounds_always_settle_and_conserve_money(self):
        rng = random.Random(42)
        for _ in range(500):
            player, dealer = Player("Ann", 100), Dealer(rng=rng)
            deck = Deck(rng=rng)
            deck.shuffle()
            game = Round(player, dealer, 10, deck)
            while game.is_player_turn:
                game.hit() if rng.random() < 0.5 else game.stand()
            game.play_dealer()
            self.assertIsNotNone(game.outcome)
            expected = {Outcome.WIN: 110, Outcome.DRAW: 100, Outcome.LOSE: 90}[game.outcome]
            self.assertEqual(player.pocket_money, expected)


class StatsTests(unittest.TestCase):
    def setUp(self):
        self.player = Player("Ann", 1000)
        self.dealer = FixedDealer()

    def play(self, bet, *ranks, hits=0):
        game = Round(self.player, self.dealer, bet, stacked_deck(*ranks))
        for _ in range(hits):
            game.hit()
        if game.is_player_turn:
            game.stand()
        game.play_dealer()
        return game

    def assertStats(self, **expected):
        stats = self.player.stats
        self.assertEqual({name: getattr(stats, name) for name in expected}, expected)

    def test_new_player_has_empty_stats(self):
        self.assertEqual(self.player.stats, PlayerStats(highest_pocket_money=1000))
        self.assertEqual(self.player.stats.win_rate, 0.0)

    def test_win(self):
        self.play(50, "10", "9", "10", "7")
        self.assertStats(rounds_played=1, wins=1, losses=0, draws=0, net_winnings=50, highest_pocket_money=1050)

    def test_draw(self):
        self.play(50, "10", "8", "10", "8")
        self.assertStats(rounds_played=1, wins=0, losses=0, draws=1, net_winnings=0, highest_pocket_money=1000)

    def test_lose_on_dealer_total(self):
        self.play(50, "10", "7", "10", "9")
        self.assertStats(rounds_played=1, losses=1, busts=0, net_winnings=-50, highest_pocket_money=1000)

    def test_bust(self):
        self.play(50, "king", "queen", "5", "2", hits=1)
        self.assertStats(rounds_played=1, losses=1, busts=1, net_winnings=-50)

    def test_blackjack(self):
        self.play(10, "ace", "king", "10", "10")
        self.assertStats(rounds_played=1, wins=1, blackjacks=1, net_winnings=10)

    def test_blackjack_counts_even_on_a_draw(self):
        self.play(10, "ace", "king", "10", "ace")
        self.assertStats(draws=1, blackjacks=1)

    def test_hitting_to_twenty_one_is_not_a_blackjack(self):
        self.play(10, "5", "6", "10", "king", "7", hits=1)
        self.assertStats(wins=1, blackjacks=0)

    def test_stats_accumulate_across_rounds(self):
        self.play(200, "10", "9", "10", "7")  # win: 1200
        self.play(50, "10", "8", "10", "8")  # draw: 1200
        self.play(200, "king", "queen", "5", "2", hits=1)  # bust: 1000
        self.play(10, "ace", "king", "10", "10")  # blackjack win: 1010
        self.assertStats(
            rounds_played=4, wins=2, losses=1, draws=1, blackjacks=1, busts=1,
            net_winnings=10, highest_pocket_money=1200,
        )
        self.assertEqual(self.player.stats.win_rate, 0.5)
        self.assertEqual(self.player.stats.summary_lines(), [
            "Rounds: 4 | Wins: 2 | Losses: 1 | Draws: 1 | Win rate: 50%",
            "Blackjacks: 1 | Busts: 1 | Net: +10$ | Best: 1200$",
        ])

    def test_random_rounds_keep_stats_consistent(self):
        rng = random.Random(7)
        player = Player("Ann", 10_000)
        for _ in range(300):
            deck = Deck(rng=rng)
            deck.shuffle()
            game = Round(player, Dealer(rng=rng), 10, deck)
            while game.is_player_turn:
                game.hit() if rng.random() < 0.5 else game.stand()
            game.play_dealer()
        stats = player.stats
        self.assertEqual(stats.rounds_played, 300)
        self.assertEqual(stats.wins + stats.losses + stats.draws, 300)
        self.assertLessEqual(stats.busts, stats.losses)
        self.assertEqual(stats.net_winnings, player.pocket_money - 10_000)
        self.assertGreaterEqual(stats.highest_pocket_money, max(player.pocket_money, 10_000))


if __name__ == "__main__":
    unittest.main()
