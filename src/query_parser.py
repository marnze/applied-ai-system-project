"""
Turns a plain-English request ("chill songs for studying") into a taste profile
that the retriever can score songs against.

This is deliberately rule-based, not AI: it is predictable, free, easy to test,
and it means the LLM only has to do one job (write the recommendations).
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

DEFAULT_ENERGY = 0.6

# Words people use -> the genre label used in songs.csv.
# Longer phrases are checked first, so "indie pop" wins over "pop".
GENRE_SYNONYMS: Dict[str, List[str]] = {
    "indie pop": ["indie pop", "indie"],
    "hip hop": ["hip hop", "hip-hop", "hiphop", "rap"],
    "r&b": ["r&b", "rnb", "r and b"],
    "lofi": ["lofi", "lo-fi", "lo fi"],
    "edm": ["edm", "electronic dance", "dance music", "house", "techno"],
    "synthwave": ["synthwave", "retrowave", "80s synth"],
    "classical": ["classical", "orchestral", "orchestra"],
    "latin": ["latin", "salsa", "bachata", "reggaeton"],
    "pop": ["pop"],
    "rock": ["rock"],
    "ambient": ["ambient"],
    "jazz": ["jazz"],
    "country": ["country"],
    "metal": ["metal"],
    "folk": ["folk"],
    "reggae": ["reggae"],
}

# Genres people might ask for that are NOT in the catalog. Recognizing them lets
# the system say "we don't have that" instead of pretending it understood nothing.
UNKNOWN_GENRES = ["k-pop", "kpop", "punk", "blues", "gospel", "opera", "trap", "drill", "afrobeats"]

MOOD_SYNONYMS: Dict[str, List[str]] = {
    "happy": ["happy", "cheerful", "upbeat", "joyful", "feel good", "feel-good", "fun"],
    "sad": ["sad", "heartbroken", "heartbreak", "breakup", "melancholy", "crying", "lonely"],
    "chill": ["chill", "chilled", "mellow", "laid back", "laid-back", "lowkey", "low-key"],
    "relaxed": ["relaxed", "relaxing", "relax", "unwind", "cozy"],
    "intense": ["intense", "hard-hitting"],
    "angry": ["angry", "rage", "mad", "furious", "aggressive"],
    "focused": ["focused", "focus", "concentrate", "concentration"],
    "peaceful": ["peaceful", "serene", "tranquil", "calm"],
    "romantic": ["romantic", "romance", "love songs", "date night"],
    "nostalgic": ["nostalgic", "nostalgia", "throwback"],
    "euphoric": ["euphoric", "rave"],
    "confident": ["confident", "swagger", "motivated", "motivation"],
    "moody": ["moody", "dark", "brooding"],
    "uplifting": ["uplifting", "hopeful", "positive", "sunny"],
    "passionate": ["passionate"],
}

# Typical energy for a mood, used when the request does not say how energetic.
MOOD_ENERGY = {
    "happy": 0.75, "sad": 0.3, "chill": 0.4, "relaxed": 0.4, "intense": 0.9,
    "angry": 0.95, "focused": 0.4, "peaceful": 0.2, "romantic": 0.5,
    "nostalgic": 0.55, "euphoric": 0.95, "confident": 0.75, "moody": 0.7,
    "uplifting": 0.65, "passionate": 0.8,
}

# Activities imply a mood (used only if no mood word was given) and an energy.
ACTIVITIES: List[Tuple[List[str], Optional[str], float]] = [
    (["study", "studying", "homework", "reading", "coding", "work"], "focused", 0.4),
    (["sleep", "sleeping", "bedtime", "meditate", "meditation"], "peaceful", 0.2),
    (["workout", "gym", "running", "run", "lifting", "exercise", "training"], "intense", 0.9),
    (["party", "dancing", "dance", "club"], "euphoric", 0.9),
    (["night drive"], "moody", 0.75),
    (["road trip", "driving", "drive", "commute"], None, 0.7),
    (["dinner", "cooking", "coffee", "morning"], "relaxed", 0.4),
    (["beach", "summer"], "uplifting", 0.65),
]

HIGH_ENERGY_WORDS = ["high energy", "high-energy", "energetic", "loud", "hype", "pump me up", "pumped", "fast"]
LOW_ENERGY_WORDS = ["low energy", "low-energy", "quiet", "soft", "slow", "gentle"]
MID_ENERGY_WORDS = ["medium energy", "moderate"]

NOT_ACOUSTIC_WORDS = ["not acoustic", "no acoustic", "electronic", "synth", "synths"]
ACOUSTIC_WORDS = ["acoustic", "unplugged", "guitar", "piano"]


@dataclass
class ParsedRequest:
    """The taste profile pulled out of a request, plus which words triggered what."""
    favorite_genre: Optional[str] = None
    favorite_mood: Optional[str] = None
    target_energy: float = DEFAULT_ENERGY
    likes_acoustic: Optional[bool] = None
    unknown_genre: Optional[str] = None
    matched: Dict[str, str] = field(default_factory=dict)

    @property
    def understood(self) -> bool:
        """True if the request contained at least one music signal."""
        return bool(self.matched)

    def to_prefs(self) -> Dict:
        return {
            "favorite_genre": self.favorite_genre,
            "favorite_mood": self.favorite_mood,
            "target_energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
        }

    def describe(self) -> str:
        acoustic = {None: "no preference", True: "yes", False: "no"}[self.likes_acoustic]
        genre = self.favorite_genre or (f"{self.unknown_genre} (not in catalog)" if self.unknown_genre else "any")
        return (f"genre={genre}, mood={self.favorite_mood or 'any'}, "
                f"energy={self.target_energy:.2f}, acoustic={acoustic}")


def _find(text: str, phrases: List[str]) -> Optional[Tuple[int, str]]:
    """Return (position, phrase) of the earliest whole-word match, or None."""
    best = None
    for phrase in sorted(phrases, key=len, reverse=True):
        match = re.search(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", text)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), phrase)
    return best


def parse_request(text: str) -> ParsedRequest:
    """Extract genre, mood, energy and acoustic preference from free text."""
    text = " " + text.lower().strip() + " "
    parsed = ParsedRequest()

    # Genre: earliest mention wins; multi-word genres are protected from "pop" etc.
    genre_hits = []
    for genre, words in GENRE_SYNONYMS.items():
        hit = _find(text, words)
        if hit:
            genre_hits.append((hit[0], -len(hit[1]), genre, hit[1]))
    if genre_hits:
        _, _, genre, word = min(genre_hits)
        parsed.favorite_genre = genre
        parsed.matched["genre"] = word
    else:
        hit = _find(text, UNKNOWN_GENRES)
        if hit:
            parsed.unknown_genre = hit[1]
            parsed.matched["unknown_genre"] = hit[1]

    # Mood: an explicit mood word beats a mood implied by an activity.
    mood_hits = []
    for mood, words in MOOD_SYNONYMS.items():
        hit = _find(text, words)
        if hit:
            mood_hits.append((hit[0], mood, hit[1]))
    if mood_hits:
        _, mood, word = min(mood_hits)
        parsed.favorite_mood = mood
        parsed.matched["mood"] = word

    activity_energy = None
    activity_hits = []
    for words, mood, energy in ACTIVITIES:
        hit = _find(text, words)
        if hit:
            activity_hits.append((hit[0], -len(hit[1]), mood, energy, hit[1]))
    if activity_hits:
        _, _, mood, energy, word = min(activity_hits)
        parsed.matched["activity"] = word
        activity_energy = energy
        if parsed.favorite_mood is None and mood is not None:
            parsed.favorite_mood = mood

    # Energy: explicit words > activity > mood default > overall default.
    if _find(text, HIGH_ENERGY_WORDS):
        parsed.target_energy = 0.9
        parsed.matched["energy"] = _find(text, HIGH_ENERGY_WORDS)[1]
    elif _find(text, LOW_ENERGY_WORDS):
        parsed.target_energy = 0.3
        parsed.matched["energy"] = _find(text, LOW_ENERGY_WORDS)[1]
    elif _find(text, MID_ENERGY_WORDS):
        parsed.target_energy = 0.6
        parsed.matched["energy"] = _find(text, MID_ENERGY_WORDS)[1]
    elif activity_energy is not None:
        parsed.target_energy = activity_energy
    elif parsed.favorite_mood:
        parsed.target_energy = MOOD_ENERGY[parsed.favorite_mood]

    # Acoustic preference: check the negative phrasing first.
    if _find(text, NOT_ACOUSTIC_WORDS):
        parsed.likes_acoustic = False
        parsed.matched["acoustic"] = _find(text, NOT_ACOUSTIC_WORDS)[1]
    elif _find(text, ACOUSTIC_WORDS):
        parsed.likes_acoustic = True
        parsed.matched["acoustic"] = _find(text, ACOUSTIC_WORDS)[1]

    return parsed
