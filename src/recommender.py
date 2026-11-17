"""
Core scoring logic for TuneJudge (the original Module 3 recommender).

In TuneJudge 2.0 this module is the *retriever*: it ranks every song in the
catalog against a taste profile, and the top songs become the context that the
AI is allowed to recommend from.
"""

import csv
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Scoring weights. These are the original TuneJudge 1.0 weights.
# (The Module 3 experiment that halved genre and doubled energy made the
# "high-energy but sad" profile worse, so TuneJudge 2.0 uses the originals.)
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 1.5
ACOUSTIC_WEIGHT = 0.5
MAX_SCORE = GENRE_WEIGHT + MOOD_WEIGHT + ENERGY_WEIGHT + ACOUSTIC_WEIGHT  # 5.0

NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")


@dataclass
class Song:
    """A song and its attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """A listener's taste preferences. likes_acoustic=None means 'no preference'."""
    favorite_genre: Optional[str]
    favorite_mood: Optional[str]
    target_energy: float
    likes_acoustic: Optional[bool]

    def to_prefs(self) -> Dict:
        return asdict(self)


def _norm(value: Optional[str]) -> str:
    """Lowercase and trim a label so 'Pop ' and 'pop' match (fixes a 1.0 bug)."""
    return (value or "").strip().lower()


def load_songs(csv_path: str) -> List[Dict]:
    """Read songs from a CSV file into dicts, converting numeric columns to int/float."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["id"] = int(row["id"])
            for field in NUMERIC_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    logger.info("Loaded %d songs from %s", len(songs), csv_path)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against the user's preferences and return (score, reasons)."""
    score = 0.0
    reasons = []

    genre = _norm(user_prefs.get("favorite_genre"))
    if genre and _norm(song["genre"]) == genre:
        score += GENRE_WEIGHT
        reasons.append(f"genre match: {song['genre']} (+{GENRE_WEIGHT:.1f})")

    mood = _norm(user_prefs.get("favorite_mood"))
    if mood and _norm(song["mood"]) == mood:
        score += MOOD_WEIGHT
        reasons.append(f"mood match: {song['mood']} (+{MOOD_WEIGHT:.1f})")

    # Closer to the target energy earns more points (not "louder is better")
    target = user_prefs["target_energy"]
    energy_points = ENERGY_WEIGHT * (1 - abs(song["energy"] - target))
    score += energy_points
    reasons.append(f"energy {song['energy']:.2f} vs target {target:.2f} (+{energy_points:.2f})")

    # Acoustic fans get acoustic songs, electronic fans get electronic songs.
    # With no stated preference every song gets the same half credit.
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is None:
        acoustic_points = ACOUSTIC_WEIGHT * 0.5
    elif likes_acoustic:
        acoustic_points = ACOUSTIC_WEIGHT * song["acousticness"]
    else:
        acoustic_points = ACOUSTIC_WEIGHT * (1 - song["acousticness"])
    score += acoustic_points
    reasons.append(f"acoustic fit (+{acoustic_points:.2f})")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort highest first (ties go to closer energy), and return the top k."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, "; ".join(reasons)))

    ranked = sorted(
        scored,
        key=lambda item: (-item[1], abs(item[0]["energy"] - user_prefs["target_energy"])),
    )
    return ranked[:k]


class Recommender:
    """Object-oriented wrapper around the scoring functions (used by the unit tests)."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        by_id = {s.id: s for s in self.songs}
        ranked = recommend_songs(user.to_prefs(), [asdict(s) for s in self.songs], k)
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        score, reasons = score_song(user.to_prefs(), asdict(song))
        return f"Score {score:.2f}/{MAX_SCORE:.1f}: " + "; ".join(reasons)
