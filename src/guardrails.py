"""
Guardrails that run before and after the AI step.

- check_request(): blocks empty, oversized, off-topic and prompt-injection input
  before anything is sent to the model.
- verify_recommendations(): checks the model's answer against the songs that
  were actually retrieved, so the AI can't recommend a song that doesn't exist.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

MAX_REQUEST_CHARS = 300

INJECTION_PATTERNS = [
    r"ignore (all |any |the |your )?(previous |prior |above )?(instructions|rules|prompt)",
    r"disregard (all |the |your )?(previous |prior |above )?(instructions|rules)",
    r"system prompt",
    r"you are now",
    r"pretend (to be|you are)",
    r"reveal (your|the) (instructions|prompt|api key)",
    r"api[_ ]?key",
]


@dataclass
class InputCheck:
    ok: bool
    reason: str = ""


def check_request(text: str) -> InputCheck:
    """Decide whether a raw user request is safe and sensible to process."""
    if text is None or not text.strip():
        return InputCheck(False, "Empty request. Describe the music you want, e.g. 'chill songs for studying'.")
    if len(text) > MAX_REQUEST_CHARS:
        return InputCheck(False, f"Request is too long ({len(text)} characters, limit {MAX_REQUEST_CHARS}).")
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return InputCheck(False, "Request looks like an attempt to change the assistant's instructions, so it was blocked.")
    return InputCheck(True)


@dataclass
class Verification:
    """Result of checking the model's picks against the retrieved songs."""
    valid: List[Dict] = field(default_factory=list)      # picks that passed
    rejected: List[str] = field(default_factory=list)    # human-readable problems
    summary: str = ""
    parse_error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.parse_error is None and not self.rejected and len(self.valid) > 0

    @property
    def total_checked(self) -> int:
        return len(self.valid) + len(self.rejected)


def _key(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def verify_recommendations(raw_reply: str, retrieved: List[Dict], max_picks: int = 3) -> Verification:
    """
    Parse the model's JSON reply and keep only picks that are real retrieved songs.

    Rules: the reply must be valid JSON with a "recommendations" list; every
    title must match a retrieved song (case-insensitive); the artist, if given,
    must match that song; every pick needs a non-empty reason; no duplicates.
    """
    result = Verification()
    try:
        data = json.loads(raw_reply)
    except (json.JSONDecodeError, TypeError):
        result.parse_error = "Reply was not valid JSON."
        return result
    if not isinstance(data, dict) or not isinstance(data.get("recommendations"), list):
        result.parse_error = "Reply did not contain a 'recommendations' list."
        return result

    result.summary = str(data.get("summary", "")).strip()
    allowed = {_key(song["title"]): song for song in retrieved}
    seen = set()

    for pick in data["recommendations"]:
        if not isinstance(pick, dict):
            result.rejected.append("A recommendation was not an object.")
            continue
        title = str(pick.get("title", "")).strip()
        why = str(pick.get("why", "")).strip()
        song = allowed.get(_key(title))
        if song is None:
            result.rejected.append(f"'{title}' is not one of the retrieved catalog songs.")
            continue
        artist = str(pick.get("artist", "")).strip()
        if artist and _key(artist) != _key(song["artist"]):
            result.rejected.append(f"'{title}' is by {song['artist']}, not {artist}.")
            continue
        if not why:
            result.rejected.append(f"'{title}' had no explanation.")
            continue
        if _key(title) in seen:
            result.rejected.append(f"'{title}' was recommended twice.")
            continue
        seen.add(_key(title))
        result.valid.append({"song": song, "why": why})

    if len(result.valid) > max_picks:
        result.valid = result.valid[:max_picks]
    return result
