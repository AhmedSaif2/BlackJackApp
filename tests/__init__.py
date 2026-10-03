import os
from unittest import mock

JEV_ENV_VARS = ("JEV_API_KEY", "TYPESAFE_API_KEY", "JEV_API_URL", "JEV_MODEL")


def without_jev():
    """Blank out the Jev settings so a default Dealer() never calls the real Jev API in tests."""
    return mock.patch.dict(os.environ, {name: "" for name in JEV_ENV_VARS})
