import io
import json
import random
import unittest
import urllib.error
from typing import List, Optional
from unittest import mock

from blackjack import Action, Card, Dealer, Deck, Outcome, Player, Round, Suit
from blackjack.jev import DEFAULT_ENDPOINT, DEFAULT_MODEL, JevClient


def fake_response(payload) -> io.BytesIO:
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


def choice_answer(choice: str):
    return {"model": "jev-1.13.0", "answers": {"decision": {"choice": choice, "confidence": 0.9}}}


class ScriptedJev(JevClient):
    """Answers with ``answers`` in order and records every state it was shown."""

    def __init__(self, *answers: Optional[str]):
        super().__init__(api_key="test-key")
        self._answers = list(answers)
        self.states: List[str] = []

    def ask_choice(self, state, instructions, criteria):
        self.states.append(state)
        return self._answers.pop(0)


class JevClientTests(unittest.TestCase):
    def test_from_env(self):
        client = JevClient.from_env({"TYPESAFE_API_KEY": "k", "JEV_API_URL": "https://proxy.test/v1", "JEV_MODEL": "jev-1.13"})
        self.assertEqual((client.api_key, client.endpoint, client.model), ("k", "https://proxy.test/v1", "jev-1.13"))

        defaults = JevClient.from_env({})
        self.assertFalse(defaults.is_configured)
        self.assertEqual((defaults.endpoint, defaults.model), (DEFAULT_ENDPOINT, DEFAULT_MODEL))

    def test_unconfigured_client_makes_no_request(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            self.assertIsNone(JevClient().ask_choice("state", "pick", {"a": "A"}))
        urlopen.assert_not_called()

    def test_sends_choice_question_and_returns_answer(self):
        client = JevClient(api_key="secret", endpoint="https://jev.test/v1/systemone", model="jev-latest")
        with mock.patch("urllib.request.urlopen", return_value=fake_response(choice_answer("stand"))) as urlopen:
            answer = client.ask_choice("my state", "hit or stand?", {"hit": "Draw", "stand": "Stop"})
        self.assertEqual(answer, "stand")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://jev.test/v1/systemone")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(json.loads(request.data), {
            "model": "jev-latest",
            "state": "my state",
            "questions": {"decision": {"type": "choice", "instructions": "hit or stand?", "criteria": {"hit": "Draw", "stand": "Stop"}}},
        })

    def test_failures_return_none(self):
        client = JevClient(api_key="secret")
        criteria = {"hit": "Draw", "stand": "Stop"}
        failures = (
            urllib.error.URLError("unreachable"),
            TimeoutError(),
            fake_response(choice_answer("double")),  # not one of the options
            fake_response({"error": "bad request"}),
            io.BytesIO(b"not json"),
        )
        for failure in failures:
            with self.subTest(failure=failure):
                patch = {"side_effect": failure} if isinstance(failure, BaseException) else {"return_value": failure}
                with mock.patch("urllib.request.urlopen", **patch):
                    self.assertIsNone(client.ask_choice("state", "pick", criteria))


class DealerJevTests(unittest.TestCase):
    def dealer_with(self, jev: JevClient, *ranks: str) -> Dealer:
        dealer = Dealer(rng=random.Random(0), jev=jev)
        for rank in ranks:
            dealer.add_card(Card(rank, Suit.CLUB))
        return dealer

    def test_jev_decides_over_the_fallback_policy(self):
        # The fallback would always hit on 12 and always stand on 20; Jev overrides both.
        self.assertIs(self.dealer_with(ScriptedJev("stand"), "10", "2").choose_action(), Action.STAND)
        self.assertIs(self.dealer_with(ScriptedJev("hit"), "10", "king").choose_action(), Action.HIT)

    def test_state_describes_hand_and_opponent(self):
        jev = ScriptedJev("hit")
        self.dealer_with(jev, "ace", "5").choose_action(opponent_total=19)
        (state,) = jev.states
        self.assertIn("Ace of Clubs, 5 of Clubs", state)
        self.assertIn("Your total: 16 (soft", state)
        self.assertIn("Player's final total: 19", state)

    def test_falls_back_when_jev_does_not_answer(self):
        self.assertIs(self.dealer_with(ScriptedJev(None), "10", "2").choose_action(), Action.HIT)
        self.assertIs(self.dealer_with(ScriptedJev(None), "10", "9").choose_action(), Action.STAND)

    def test_round_plays_dealer_turn_with_jev(self):
        # Player stands on 19; the dealer has 10 and Jev hits once (10 + 6), then stands.
        jev = ScriptedJev("hit", "stand")
        deck = Deck([Card(rank, Suit.HEART) for rank in reversed(("10", "9", "10", "6", "king"))])
        game = Round(Player("Ann", 100), Dealer(jev=jev), 10, deck)
        game.stand()
        game.play_dealer()
        self.assertEqual(game.dealer.hand.total, 16)
        self.assertIs(game.outcome, Outcome.WIN)
        self.assertEqual(len(jev.states), 2)
        self.assertTrue(all("Player's final total: 19" in state for state in jev.states))


if __name__ == "__main__":
    unittest.main()
