"""
Command line interface for TuneJudge 2.0.

Examples:
    python -m src.main "chill songs for studying"     # one request
    python -m src.main                                 # interactive mode
    python -m src.main --no-ai "sad acoustic songs"    # rules only, no API call
    python -m src.main --trace "gym rock"              # also print each pipeline step
    python -m src.main --profiles                      # original 1.0 profile demo
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from src.llm_client import get_llm_client
from src.pipeline import ROOT, Result, TuneJudge
from src.recommender import MAX_SCORE, load_songs, recommend_songs

LOG_DIR = ROOT / "logs"

# Taste profiles from TuneJudge 1.0, kept so the original demo still runs.
PROFILES = {
    "Happy pop fan": {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.80, "likes_acoustic": False},
    "Calm study listener": {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.40, "likes_acoustic": True},
    "Deep intense rock": {"favorite_genre": "rock", "favorite_mood": "intense", "target_energy": 0.90, "likes_acoustic": False},
    "Conflicted: high-energy but sad": {"favorite_genre": "folk", "favorite_mood": "sad", "target_energy": 0.90, "likes_acoustic": False},
    "Acoustic metalhead": {"favorite_genre": "metal", "favorite_mood": "angry", "target_energy": 0.95, "likes_acoustic": True},
    "Genre not in catalog": {"favorite_genre": "k-pop", "favorite_mood": "happy", "target_energy": 0.70, "likes_acoustic": False},
    "Capitalized input": {"favorite_genre": "Pop", "favorite_mood": "Happy", "target_energy": 0.80, "likes_acoustic": False},
}


def setup_logging() -> None:
    """Write detailed logs to logs/tunejudge.log; keep the terminal clean."""
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "tunejudge.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def print_result(result: Result, show_trace: bool = False) -> None:
    print("=" * 64)
    print(f"Request: {result.request}")
    if result.status == "blocked":
        print(f"BLOCKED by guardrail: {result.message}")
        if show_trace:
            print_trace(result)
        print()
        return
    print(f"Understood: {result.profile.describe()}")
    print(f"Retrieved {len(result.retrieved)} songs: "
          + ", ".join(f"{i['song']['title']} ({i['score']:.2f})" for i in result.retrieved))
    if result.genre_notes:
        print(f"Genre notes used: {', '.join(result.genre_notes)}")
    print(f"Mode: {result.mode} | Confidence: {result.confidence:.2f} ({result.confidence_label})")
    print("-" * 64)
    if result.summary:
        print(result.summary)
    for rank, pick in enumerate(result.picks, start=1):
        print(f"{rank}. {pick.title} by {pick.artist}  [{pick.genre}, {pick.mood}]")
        print(f"     {pick.why}")
    for warning in result.warnings:
        print(f"! {warning}")
    if show_trace:
        print_trace(result)
    print()


def print_trace(result: Result) -> None:
    print("Trace:")
    for step in result.trace:
        print(f"  - {step}")


def save_trace(result: Result) -> None:
    """Append the run's reasoning steps to logs/agent_traces.md (for ai_interactions.md)."""
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_DIR / "agent_traces.md", "a", encoding="utf-8") as f:
        f.write(f"\n### {datetime.now():%Y-%m-%d %H:%M} | {result.request!r}\n\n")
        for step in result.trace:
            f.write(f"- {step}\n")
        for pick in result.picks:
            f.write(f"- pick: {pick.title} by {pick.artist}: {pick.why}\n")


def ask_feedback(result: Result) -> None:
    """Human-in-the-loop: let the listener rate the picks; saved for later review."""
    if result.status != "ok":
        return
    answer = input("Were these good picks? [y/n/skip]: ").strip().lower()
    if answer not in ("y", "n"):
        return
    LOG_DIR.mkdir(exist_ok=True)
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "request": result.request,
        "mode": result.mode,
        "confidence": result.confidence,
        "picks": [p.title for p in result.picks],
        "helpful": answer == "y",
    }
    with open(LOG_DIR / "feedback.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print("Thanks, feedback saved to logs/feedback.jsonl")


def run_profiles() -> None:
    """The original TuneJudge 1.0 demo: fixed profiles, rule-based scores."""
    songs = load_songs(str(ROOT / "data" / "songs.csv"))
    for name, prefs in PROFILES.items():
        print("=" * 60)
        print(f"Profile: {name}")
        print("=" * 60)
        for rank, (song, score, explanation) in enumerate(recommend_songs(prefs, songs, k=5), start=1):
            print(f"{rank}. {song['title']} by {song['artist']}  [score {score:.2f} / {MAX_SCORE:.2f}]")
            for reason in explanation.split("; "):
                print(f"     - {reason}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="TuneJudge 2.0: AI music recommendations grounded in a catalog.")
    parser.add_argument("request", nargs="*", help="what you want to listen to")
    parser.add_argument("--no-ai", action="store_true", help="skip Gemini and use rule-based picks only")
    parser.add_argument("--trace", action="store_true", help="print every pipeline step")
    parser.add_argument("--save-trace", action="store_true", help="append steps to logs/agent_traces.md")
    parser.add_argument("--profiles", action="store_true", help="run the original 1.0 profile demo")
    args = parser.parse_args()

    setup_logging()
    if args.profiles:
        run_profiles()
        return

    llm = None if args.no_ai else get_llm_client()
    judge = TuneJudge(llm=llm)
    print(f"TuneJudge 2.0 | AI: {llm.name if llm else 'off (rules only)'}\n")

    if args.request:
        result = judge.run(" ".join(args.request))
        print_result(result, args.trace)
        if args.save_trace:
            save_trace(result)
        return

    print("Describe what you want to hear (blank line to quit).")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        result = judge.run(text)
        print_result(result, args.trace)
        if args.save_trace:
            save_trace(result)
        ask_feedback(result)


if __name__ == "__main__":
    main()
