import random
import streamlit as st

from logic_utils import (
    get_range_for_difficulty,
    parse_guess,
    check_guess,
    update_score,
    load_high_scores,
    save_high_score,
    guess_proximity_pct,
    hot_cold_label,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

# ── Sidebar: Settings ──────────────────────────────────────────────────────────

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# ── Sidebar: High Scores ───────────────────────────────────────────────────────
# Scores are read from highscores.json on every render so they stay fresh
# after a new record is set mid-session.

st.sidebar.divider()
st.sidebar.subheader("🏆 High Scores")

high_scores = load_high_scores()
for diff in ["Easy", "Normal", "Hard"]:
    best = high_scores.get(diff, "—")
    # Mark the currently active difficulty so the player knows where they stand
    active_marker = " ◀" if diff == difficulty else ""
    st.sidebar.caption(f"**{diff}:** {best}{active_marker}")

# ── Session state initialization ───────────────────────────────────────────────
# Switching difficulty resets the whole game so the secret stays in range.
# history stores dicts so the visualisation can colour bars by outcome.

if "secret" not in st.session_state or st.session_state.get("difficulty") != difficulty:
    st.session_state.secret = random.randint(low, high)
    st.session_state.difficulty = difficulty
    st.session_state.attempts = 1
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []  # list of {"guess": int|str, "outcome": str}

if "attempts" not in st.session_state:
    st.session_state.attempts = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

# ── Sidebar: Guess History Visualization ───────────────────────────────────────
# Each valid guess is rendered as a progress bar showing its position inside the
# allowed range.  The secret is revealed as a separate bar only once the game
# ends, giving the player a satisfying "ah, that close!" moment.

if st.session_state.history:
    st.sidebar.divider()
    st.sidebar.subheader("📊 Guess History")
    st.sidebar.caption(f"← {low} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {high} →")

    game_over = st.session_state.status != "playing"

    for entry in st.session_state.history:
        guess = entry["guess"]
        outcome = entry["outcome"]

        if outcome == "Win":
            icon = "🟢"
        elif outcome == "Too High":
            icon = "🔴"
        elif outcome == "Too Low":
            icon = "🔵"
        else:
            # Invalid / unparseable input — skip the bar, just show the raw text
            st.sidebar.caption(f"⚪ _{guess}_ (invalid)")
            continue

        pct = guess_proximity_pct(guess, low, high)
        st.sidebar.progress(pct, text=f"{icon} {guess}")

    # After the game ends reveal exactly where the secret was
    if game_over:
        secret_pct = guess_proximity_pct(st.session_state.secret, low, high)
        st.sidebar.progress(secret_pct, text=f"🎯 Secret: {st.session_state.secret}")

# ── Main game area ─────────────────────────────────────────────────────────────

st.subheader("Make a guess")

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.history = []
    st.session_state.status = "playing"
    st.session_state.score = 0
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")

    # ── End-of-game summary table ──────────────────────────────────────────
    # Build one row per valid guess so the player can review every move.
    valid_entries = [e for e in st.session_state.history if e["outcome"] != "invalid"]
    if valid_entries:
        st.subheader("📋 Game Summary")
        rows = []
        for i, entry in enumerate(valid_entries, start=1):
            guess = entry["guess"]
            outcome = entry["outcome"]
            distance = abs(guess - st.session_state.secret)
            temp_emoji, temp_label = hot_cold_label(
                guess, st.session_state.secret, low, high
            )
            outcome_display = {
                "Win": "🟢 Win",
                "Too High": "🔴 Too High",
                "Too Low": "🔵 Too Low",
            }.get(outcome, outcome)
            rows.append({
                "Attempt": i,
                "Guess": guess,
                "Result": outcome_display,
                "Distance": distance,
                "Temperature": f"{temp_emoji} {temp_label}",
            })
        st.table(rows)

    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        # Record the bad input so the sidebar history stays consistent
        st.session_state.history.append({"guess": raw_guess, "outcome": "invalid"})
        st.error(err)
    else:
        outcome = check_guess(guess_int, st.session_state.secret)

        # Every valid guess goes into history for the visualisation
        st.session_state.history.append({"guess": guess_int, "outcome": outcome})

        if show_hint and outcome != "Win":
            # Color-coded direction hint: blue = go higher, orange = go lower
            temp_emoji, temp_label = hot_cold_label(guess_int, st.session_state.secret, low, high)
            if outcome == "Too High":
                st.warning(f"📉 Go **LOWER**! &nbsp; {temp_emoji} {temp_label}")
            else:
                st.info(f"📈 Go **HIGHER**! &nbsp; {temp_emoji} {temp_label}")

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"

            # Persist the score and congratulate on a new personal best
            is_new_best = save_high_score(difficulty, st.session_state.score)
            if is_new_best:
                st.toast(f"🏆 New high score for {difficulty}: {st.session_state.score}!")

            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
