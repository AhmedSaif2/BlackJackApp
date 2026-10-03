import json
import os
import unittest
from pathlib import Path
from unittest import mock

from blackjack import Player, PlayerStats
from blackjack.game import PLAYER_NAME, STARTING_POCKET_MONEY
from blackjack.save import SAVE_FILE_ENV, SaveFile, default_save_path
from tests import temp_save


class SaveFileTests(unittest.TestCase):
    def setUp(self):
        self.save = temp_save(self)

    def assertFreshPlayer(self, player):
        self.assertEqual(player.name, PLAYER_NAME)
        self.assertEqual(player.pocket_money, STARTING_POCKET_MONEY)
        self.assertEqual(player.stats, PlayerStats(highest_pocket_money=STARTING_POCKET_MONEY))

    def test_no_save_starts_a_fresh_player(self):
        self.assertFreshPlayer(self.save.load())

    def test_round_trip(self):
        player = Player(PLAYER_NAME, 3100)
        player.stats = PlayerStats(rounds_played=5, wins=3, losses=1, draws=1, blackjacks=1, busts=1,
                                   net_winnings=600, highest_pocket_money=3300)
        self.save.save(player)
        loaded = self.save.load()
        self.assertEqual(loaded.pocket_money, 3100)
        self.assertEqual(loaded.stats, player.stats)

    def test_creates_the_folder(self):
        save = SaveFile(self.save.path.parent / "nested" / "save.json")
        save.save(Player(PLAYER_NAME, 10))
        self.assertEqual(save.load().pocket_money, 10)

    def test_unreadable_saves_start_fresh(self):
        for content in ("not json", "[]", "{}", '{"pocket_money": "lots"}', '{"pocket_money": -5}',
                        '{"pocket_money": 100, "stats": {"wins": "many"}}', '{"pocket_money": 100, "stats": 3}'):
            with self.subTest(content=content):
                self.save.path.write_text(content, encoding="utf-8")
                self.assertFreshPlayer(self.save.load())

    def test_unknown_and_missing_stats_are_tolerated(self):
        self.save.path.write_text(json.dumps({"pocket_money": 900, "stats": {"wins": 2, "streak": 7}}), encoding="utf-8")
        loaded = self.save.load()
        self.assertEqual(loaded.stats.wins, 2)
        self.assertEqual(loaded.stats.rounds_played, 0)
        self.assertEqual(loaded.stats.highest_pocket_money, 900)

    def test_save_failure_is_ignored(self):
        # The "folder" is a file, so the save can't be written; the game must carry on.
        blocker = self.save.path.parent / "blocker"
        blocker.write_text("", encoding="utf-8")
        SaveFile(blocker / "save.json").save(Player(PLAYER_NAME, 10))


class DefaultPathTests(unittest.TestCase):
    def test_env_var_overrides_the_location(self):
        with mock.patch.dict(os.environ, {SAVE_FILE_ENV: "/tmp/elsewhere.json"}):
            self.assertEqual(default_save_path(), Path("/tmp/elsewhere.json"))
            self.assertEqual(SaveFile().path, Path("/tmp/elsewhere.json"))

    def test_default_lives_in_the_user_config_folder(self):
        with mock.patch.dict(os.environ, {SAVE_FILE_ENV: ""}):
            path = default_save_path()
        self.assertEqual(path.name, "save.json")
        self.assertEqual(path.parent.name, "BlackjackApp")


if __name__ == "__main__":
    unittest.main()
