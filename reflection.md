# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
  - The game UI loaded and appeared functional — you could enter a guess and click Submit. However, the hints were unreliable and the game could not be won consistently. Running the tests immediately showed all 3 failing with `NotImplementedError`, meaning the core logic had never been wired up properly.
- List at least two concrete bugs you noticed at the start
  (for example: "the secret number kept changing" or "the hints were backwards").
  - **The hints were wrong on every other guess.** On even-numbered attempts, `app.py` converted the secret number to a string before comparing, so the comparison used lexicographic (alphabetical) order instead of numeric order. For example, guessing 60 when the secret was 50 could return "Too Low" instead of "Too High" because `"60" < "50"` alphabetically is false but string comparison of numbers doesn't work like math.
  - **`logic_utils.py` was all stubs — nothing worked.** Every function (`check_guess`, `parse_guess`, `get_range_for_difficulty`, `update_score`) raised `NotImplementedError`. The tests imported from `logic_utils`, so all 3 tests failed immediately without even running any game logic.

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
  Claude Code
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
  - Claude correctly identified the even-attempt string conversion bug in `app.py` at lines 158–163, where `secret` was cast to a string every other turn causing wrong hints. It explained that string comparison of numbers uses lexicographic order (so `"9" > "50"` is true alphabetically), which is exactly why the hints were unreliable. I verified this by reading the code myself and tracing what happens on attempt 2: `secret = str(50)` → `"50"`, then `check_guess(60, "50")` compares an int to a string, triggering the fallback `str(guess) > secret` path which gives the wrong result.
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).
  - Claude initially tried to start the Streamlit app in the background with `--server.headless true` before I had a chance to review what it was doing. I stopped it because launching a server process without understanding the codebase first is the wrong order of operations — you should read and test the logic before running the full app. The better approach was to run `pytest` first, which gave clearer, faster feedback about what was broken.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
  - A fix was only considered real when `pytest` passed for the relevant test. Reading the code and reasoning about it was useful for understanding the bug, but the test result was the actual verification. If the test still failed after a change, the fix was not done.
- Describe at least one test you ran (manual or using pytest)
  and what it showed you about your code.
  - Running `python -m pytest tests/test_game_logic.py -v` showed all three tests failing immediately with `NotImplementedError: Refactor this function from app.py into logic_utils.py`. This was useful because it confirmed the problem wasn't logic errors — the functions simply hadn't been implemented yet. It also showed that the test file imports `check_guess` from `logic_utils`, not from `app.py`, which meant the working version in `app.py` was completely disconnected from the tests.
- Did AI help you design or understand any tests? How?
  - Yes — Claude read both the test file and `logic_utils.py` together and pointed out that the tests assert `result == "Win"` (a plain string), but the `app.py` version of `check_guess` returns a tuple like `("Win", "🎉 Correct!")`. That mismatch meant even if the functions were copied over unchanged, the tests would still fail. This shaped the fix: `check_guess` in `logic_utils.py` needed to return just the outcome string, and the message display needed to be handled separately in `app.py`.

---

## 4. What did you learn about Streamlit and state?

- In your own words, explain why the secret number kept changing in the original app.
- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
- What change did you make that finally gave the game a stable secret number?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
