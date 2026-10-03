import os
import tempfile
from pathlib import Path
from unittest import mock

from blackjack.save import SaveFile

JEV_ENV_VARS = ("JEV_API_KEY", "TYPESAFE_API_KEY", "JEV_API_URL", "JEV_MODEL")


def without_jev():
    """Blank out the Jev settings so a default Dealer() never calls the real Jev API in tests."""
    return mock.patch.dict(os.environ, {name: "" for name in JEV_ENV_VARS})


def temp_save(test) -> SaveFile:
    """A SaveFile in a temporary directory removed after ``test``, so tests never touch the real save."""
    directory = tempfile.TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    return SaveFile(Path(directory.name) / "save.json")
