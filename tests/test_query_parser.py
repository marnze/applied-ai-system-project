import pytest

from src.query_parser import parse_request


def test_mood_and_activity():
    p = parse_request("chill songs for studying")
    assert p.favorite_mood == "chill"          # explicit mood beats the activity's mood
    assert p.target_energy == pytest.approx(0.4)
    assert p.favorite_genre is None


def test_multi_word_genre_beats_single_word():
    assert parse_request("indie pop for a sunny afternoon").favorite_genre == "indie pop"


def test_genre_synonyms_and_case():
    assert parse_request("Hip-Hop to get motivated").favorite_genre == "hip hop"
    assert parse_request("some LO-FI beats").favorite_genre == "lofi"


def test_explicit_energy_overrides_activity():
    assert parse_request("quiet music for the gym").target_energy == pytest.approx(0.3)


def test_acoustic_negation():
    assert parse_request("acoustic folk").likes_acoustic is True
    assert parse_request("jazz but not acoustic").likes_acoustic is False


def test_unknown_genre_is_flagged_not_matched_as_pop():
    p = parse_request("k-pop for a party")
    assert p.favorite_genre is None
    assert p.unknown_genre == "k-pop"


def test_off_topic_request_is_not_understood():
    assert not parse_request("what is the capital of France").understood
