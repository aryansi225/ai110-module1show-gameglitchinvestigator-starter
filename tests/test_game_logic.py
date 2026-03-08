import os
import json
import tempfile

from logic_utils import check_guess, parse_guess, guess_proximity_pct, load_high_scores, save_high_score

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


def test_parse_guess_valid_integer():
    ok, value, err = parse_guess("42")
    assert ok is True
    assert value == 42
    assert err is None


def test_parse_guess_empty_string():
    ok, value, err = parse_guess("")
    assert ok is False
    assert value is None
    assert err is not None


def test_parse_guess_none():
    ok, value, err = parse_guess(None)
    assert ok is False
    assert value is None
    assert err is not None


def test_parse_guess_non_numeric():
    ok, value, err = parse_guess("abc")
    assert ok is False
    assert value is None
    assert err is not None


def test_parse_guess_float_string():
    # Floats should be truncated to int rather than rejected
    ok, value, err = parse_guess("3.7")
    assert ok is True
    assert value == 3
    assert err is None


# ── guess_proximity_pct ────────────────────────────────────────────────────────

def test_proximity_low_end():
    # A guess equal to the range minimum maps to 0.0
    assert guess_proximity_pct(1, 1, 100) == 0.0


def test_proximity_high_end():
    # A guess equal to the range maximum maps to 1.0
    assert guess_proximity_pct(100, 1, 100) == 1.0


def test_proximity_midpoint():
    # A guess exactly in the middle maps to 0.5
    assert guess_proximity_pct(50, 0, 100) == 0.5


def test_proximity_clamps_below_zero():
    # A guess below the range floor is clamped to 0.0
    assert guess_proximity_pct(-5, 1, 100) == 0.0


def test_proximity_clamps_above_one():
    # A guess above the range ceiling is clamped to 1.0
    assert guess_proximity_pct(200, 1, 100) == 1.0


def test_proximity_zero_width_range():
    # When low == high there is only one valid guess, treat it as exact (1.0)
    assert guess_proximity_pct(5, 5, 5) == 1.0


# ── high score persistence ─────────────────────────────────────────────────────

def test_load_high_scores_missing_file():
    # A path that does not exist should return an empty dict, not raise
    scores = load_high_scores("/tmp/does_not_exist_xyz.json")
    assert scores == {}


def test_save_and_load_high_score():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        # First save should succeed and record the new best
        is_new = save_high_score("Normal", 80, filepath=path)
        assert is_new is True
        assert load_high_scores(path)["Normal"] == 80
    finally:
        os.unlink(path)


def test_save_high_score_not_beaten():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_high_score("Easy", 90, filepath=path)
        # A lower score should NOT overwrite the existing best
        is_new = save_high_score("Easy", 50, filepath=path)
        assert is_new is False
        assert load_high_scores(path)["Easy"] == 90
    finally:
        os.unlink(path)


def test_save_high_score_different_difficulties():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_high_score("Easy", 70, filepath=path)
        save_high_score("Hard", 40, filepath=path)
        scores = load_high_scores(path)
        assert scores["Easy"] == 70
        assert scores["Hard"] == 40
    finally:
        os.unlink(path)
