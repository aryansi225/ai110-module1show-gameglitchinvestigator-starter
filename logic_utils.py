import json
import os


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 50
    if difficulty == "Hard":
        return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return the outcome string.

    Returns: "Win", "Too High", or "Too Low"
    """
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score


# ── High score persistence ─────────────────────────────────────────────────────

HIGHSCORE_FILE = "highscores.json"


def load_high_scores(filepath: str = HIGHSCORE_FILE) -> dict:
    """Load per-difficulty high scores from a JSON file.

    Returns an empty dict if the file doesn't exist or is corrupt,
    so callers never have to handle missing-file errors themselves.
    """
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_high_score(difficulty: str, score: int, filepath: str = HIGHSCORE_FILE) -> bool:
    """Persist a new high score for the given difficulty if it beats the current best.

    Returns True when a new record was set, False when the existing best stands.
    This lets the caller decide whether to show a congratulatory message.
    """
    scores = load_high_scores(filepath)
    current_best = scores.get(difficulty, 0)

    if score > current_best:
        scores[difficulty] = score
        with open(filepath, "w") as f:
            json.dump(scores, f, indent=2)
        return True

    return False


# ── Guess visualisation helper ─────────────────────────────────────────────────

def guess_proximity_pct(guess: int, low: int, high: int) -> float:
    """Return where *guess* falls in [low, high] as a fraction between 0.0 and 1.0.

    Used to drive Streamlit progress bars so the player can see at a glance how
    close each previous guess was to the edges of the allowed range — and, once
    the game ends, how close they were to the secret number.

    Edge cases:
    - If the range has zero width the guess is trivially correct, so return 1.0.
    - Clamp to [0, 1] to guard against out-of-range guesses (the UI allows them).
    """
    span = high - low
    if span == 0:
        return 1.0
    return max(0.0, min(1.0, (guess - low) / span))
