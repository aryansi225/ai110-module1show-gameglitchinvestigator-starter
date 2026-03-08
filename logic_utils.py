import json
import os


HIGHSCORE_FILE = "highscores.json"


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return the inclusive numeric range for a given difficulty level.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"``, or ``"Hard"``.

    Returns:
        A ``(low, high)`` tuple of integers defining the guessable range.

    Examples:
        >>> get_range_for_difficulty("Easy")
        (1, 20)
        >>> get_range_for_difficulty("Hard")
        (1, 100)
    """
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 50
    if difficulty == "Hard":
        return 1, 100


def parse_guess(raw: str) -> tuple[bool, int | None, str | None]:
    """Parse raw text input from the player into a validated integer guess.

    Accepts plain integers (``"42"``) and decimal strings (``"3.7"``),
    truncating floats toward zero rather than rejecting them outright.

    Args:
        raw: The unvalidated string typed by the player, or ``None`` when
            the input widget has not yet been touched.

    Returns:
        A three-element tuple ``(ok, value, error)``:

        - ``ok`` (bool): ``True`` when parsing succeeded.
        - ``value`` (int | None): The parsed integer on success, else ``None``.
        - ``error`` (str | None): A human-readable message on failure, else ``None``.

    Examples:
        >>> parse_guess("42")
        (True, 42, None)
        >>> parse_guess("")
        (False, None, 'Enter a guess.')
        >>> parse_guess("abc")
        (False, None, 'That is not a number.')
        >>> parse_guess("3.7")
        (True, 3, None)
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


def check_guess(guess: int, secret: int) -> str:
    """Compare a player's guess to the secret number and return the outcome.

    Args:
        guess: The integer value guessed by the player.
        secret: The secret integer the player is trying to find.

    Returns:
        One of three outcome strings:

        - ``"Win"``      – the guess exactly matches the secret.
        - ``"Too High"`` – the guess is above the secret.
        - ``"Too Low"``  – the guess is below the secret.

    Examples:
        >>> check_guess(50, 50)
        'Win'
        >>> check_guess(60, 50)
        'Too High'
        >>> check_guess(40, 50)
        'Too Low'
    """
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Compute an updated score after a single guess.

    Scoring rules:

    - **Win**: awards ``max(10, 100 - 10 * (attempt_number + 1))`` points,
      rewarding players who find the secret quickly.
    - **Too High on an even attempt**: awards 5 bonus points (the game rewards
      consistent overshooting as a deliberate strategy).
    - **Too High on an odd attempt** or **Too Low**: deducts 5 points.
    - Any other outcome (e.g. an unrecognised string): score is unchanged.

    Args:
        current_score: The player's score before this guess.
        outcome: The result string from :func:`check_guess`
            (``"Win"``, ``"Too High"``, or ``"Too Low"``).
        attempt_number: The 1-based attempt index for the current guess,
            used to scale the win bonus and determine the parity penalty.

    Returns:
        The updated integer score.

    Examples:
        >>> update_score(0, "Win", 1)
        70
        >>> update_score(50, "Too Low", 3)
        45
    """
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

def load_high_scores(filepath: str = HIGHSCORE_FILE) -> dict:
    """Load per-difficulty high scores from a JSON file.

    The file is expected to be a flat JSON object whose keys are difficulty
    names (``"Easy"``, ``"Normal"``, ``"Hard"``) and whose values are integer
    scores, e.g. ``{"Easy": 90, "Hard": 40}``.

    Args:
        filepath: Path to the JSON file.  Defaults to :data:`HIGHSCORE_FILE`
            (``"highscores.json"`` in the working directory).

    Returns:
        A dict mapping difficulty name to best score.  Returns an empty dict
        when the file does not exist or contains invalid JSON, so callers never
        need to handle I/O errors themselves.

    Examples:
        >>> load_high_scores("/tmp/nonexistent.json")
        {}
    """
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_high_score(
    difficulty: str,
    score: int,
    filepath: str = HIGHSCORE_FILE,
) -> bool:
    """Persist a new high score for the given difficulty if it beats the current best.

    Reads the existing scores from *filepath*, updates the entry for
    *difficulty* only when *score* is strictly greater than the stored value,
    then writes the file back atomically via a standard ``open`` + ``json.dump``.

    Args:
        difficulty: The difficulty level the score was achieved on
            (``"Easy"``, ``"Normal"``, or ``"Hard"``).
        score: The final score to compare against the stored best.
        filepath: Path to the JSON scores file.  Defaults to
            :data:`HIGHSCORE_FILE`.

    Returns:
        ``True`` when a new record was saved; ``False`` when the existing best
        was not beaten.  The caller can use this to decide whether to display
        a congratulatory notification.

    Examples:
        >>> import tempfile, os
        >>> f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        >>> save_high_score("Normal", 80, filepath=f.name)
        True
        >>> save_high_score("Normal", 50, filepath=f.name)
        False
        >>> os.unlink(f.name)
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
    """Return where *guess* sits within ``[low, high]`` as a fraction in ``[0.0, 1.0]``.

    The result is suitable for passing directly to ``st.progress()`` so the
    player can see at a glance how each previous guess relates to the full
    allowed range — and, once the game ends, how close they were to the secret.

    Args:
        guess: The integer value whose position should be computed.
        low: The inclusive lower bound of the guessable range.
        high: The inclusive upper bound of the guessable range.

    Returns:
        A float in ``[0.0, 1.0]``:

        - ``0.0`` when *guess* is at or below *low*.
        - ``1.0`` when *guess* is at or above *high*.
        - A proportional value in between otherwise.

        When ``low == high`` the range has zero width and ``1.0`` is returned
        unconditionally to avoid a division-by-zero error.

    Examples:
        >>> guess_proximity_pct(1, 1, 100)
        0.0
        >>> guess_proximity_pct(100, 1, 100)
        1.0
        >>> guess_proximity_pct(50, 0, 100)
        0.5
        >>> guess_proximity_pct(200, 1, 100)
        1.0
    """
    span = high - low
    if span == 0:
        return 1.0
    return max(0.0, min(1.0, (guess - low) / span))
