"""
Minimal Google Gemini client using only the Python standard library.

The API key is read from the GEMINI_API_KEY environment variable or a local
.env file. It is sent in a request header (never in the URL) and never logged.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class LLMError(Exception):
    """Raised when the model can't be reached or returns something unusable."""


def load_env_file(path: str = ".env") -> None:
    """Load KEY=value lines from a .env file into os.environ (without overwriting)."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class GeminiClient:
    """Sends a prompt to Gemini and returns the text of the reply."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: float = 30.0):
        if not api_key:
            raise ValueError("A Gemini API key is required")
        self._api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def name(self) -> str:
        return f"Gemini ({self.model})"

    def generate(self, prompt: str, system: str = "", json_output: bool = True) -> str:
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_output:
            body["generationConfig"]["responseMimeType"] = "application/json"

        request = urllib.request.Request(
            API_URL.format(model=self.model),
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self._api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")[:300]
            raise LLMError(f"Gemini returned HTTP {err.code}: {detail}") from err
        except (urllib.error.URLError, TimeoutError) as err:
            raise LLMError(f"Could not reach Gemini: {err}") from err
        except json.JSONDecodeError as err:
            raise LLMError("Gemini returned a response that was not JSON") from err

        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as err:
            raise LLMError(f"Unexpected Gemini response shape: {str(data)[:300]}") from err


def get_llm_client() -> Optional[GeminiClient]:
    """Return a Gemini client if a key is configured, otherwise None (rules-only mode)."""
    load_env_file()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your-key-here":
        logger.warning("No GEMINI_API_KEY found; running in rules-only mode")
        return None
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return GeminiClient(api_key, model=model)
