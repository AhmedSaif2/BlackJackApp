"""Client for Jev, TypeSafe AI's "System One" model.

Jev doesn't generate text: it takes a ``state`` plus typed ``questions`` and returns
calibrated decisions. The dealer uses a single ``choice`` question to decide whether
to hit or stand.

Configuration (environment variables):

- ``JEV_API_KEY`` (or ``TYPESAFE_API_KEY``): required; without it Jev is disabled.
- ``JEV_API_URL``: defaults to ``https://api.typesafe.ai/v1/systemone``.
- ``JEV_MODEL``: defaults to ``jev-latest``.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict, Mapping, Optional

DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT_SECONDS = 3.0


class JevClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = DEFAULT_ENDPOINT,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> "JevClient":
        return cls(
            api_key=environ.get("JEV_API_KEY") or environ.get("TYPESAFE_API_KEY"),
            endpoint=environ.get("JEV_API_URL") or DEFAULT_ENDPOINT,
            model=environ.get("JEV_MODEL") or DEFAULT_MODEL,
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def ask_choice(self, state: str, instructions: str, criteria: Dict[str, str]) -> Optional[str]:
        """Ask Jev one ``choice`` question and return the chosen option id.

        Returns None when Jev isn't configured, the request fails, or the answer isn't
        one of ``criteria``'s keys, so callers can fall back to their own logic.
        """
        if not self.is_configured:
            return None
        body = {
            "model": self.model,
            "state": state,
            "questions": {
                "decision": {"type": "choice", "instructions": instructions, "criteria": criteria},
            },
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
            choice = payload["answers"]["decision"]["choice"]
        except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
            # Network errors, timeouts, non-2xx responses or unexpected payloads.
            return None
        return choice if choice in criteria else None
