# Session 5 Overnight Report — mechanical pass

Branch: `session5/mechanical` (cut from `main`)
Venv confirmed: `which python` → `/Users/arnavhmutt/Desktop/aviation-ds-projects/.venvs/aerograph/bin/python` (after `source .../bin/activate`; the bare unsourced shell resolves `python` to `/opt/homebrew/bin/python`, so every command below was run inside the activated venv explicitly).

No commits, no `git add`, no pushes were made. All changes are sitting in the working tree on `session5/mechanical`.

---

## Task 1 — State report (read-only)

### `git status` (before any edits)

```
On branch session5/mechanical
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   .gitignore

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	scripts/19_groq_probe.py
	scripts/20_groq_tool_probe.py

no changes added to commit (use "git add" and/or "git commit -a")
```

### `git log -1 --stat`

```
commit 7061c0f0c7ac9baec80a06c61e42879dd0c135ed
Author: arnavhm <arnavhmutt@gmail.com>
Date:   Fri Aug 14 20:19:36 2026 +0530

    Gate C complete: Groq provider, snapshot+dialect prompt fixes, Option A trap scoping. First run with all 10 tests reaching a verdict.

 agent/llm.py                  | 238 +++++++++++++++++++++++++++++++++++++++++-
 agent/prompts.py              |  15 +++
 scripts/17_agent_gate.py      |  38 +++++--
 scripts/18_oracle_selftest.py |   8 ++
 4 files changed, 290 insertions(+), 9 deletions(-)
```

### `git ls-files scripts/17_agent_gate.py`

```
scripts/17_agent_gate.py
```

Exit code 0, one line returned → **tracked**.

---

## Task 2 — Triage (before any edit)

### P2: stray `=` in `scripts/13_connect_test.py`

**OUTSTANDING** (at triage time). Evidence, `scripts/13_connect_test.py:18` (pre-fix):

```python
rec = s.run("RETURN 1 AS ok, datetime() AS now =").single()
```

Trailing `=` inside the Cypher string, before the closing quote — not valid Cypher syntax for a bare `RETURN`.

### P5: empty `killer_query.cypher/` directory

**OUTSTANDING** (at triage time). `find . -iname "*killer_query*"` returned two hits:
- `./killer_query.cypher` — a directory, `ls -la` showed only `.` and `..` (empty), untracked by git (`git ls-files | grep -i "killer_query.cypher/"` returned nothing).
- `./cypher/killer_query.cypher` — the real file, 1524 bytes, ASCII text.

The stray directory at repo root is distinct from the actual query file under `cypher/`.

### P6: two poisoned transcript cache entries

**AMBIGUOUS — not resolved, nothing deleted.** See "Questions for Arnav" below. Summary: `.agent_cache/` holds 22 entries. None have a non-null `error` field (consistent with the caching-error-responses fix already being in place — see next item). Filtering for entries with empty `final_text` despite `api_calls > 1` (i.e., a run that made real queries but never produced a cacheable-looking answer, then got cached anyway since `run.error` stayed `None`) surfaced **three** candidates, not two:

- `49375c73230d4a102ce46e42.json` — question "Which aircraft should we swap before its flight departs today...", one failed attempt (real `CypherSyntaxError`), stored `2026-08-14T19:17:28`.
- `6ad74f798ed07a4275d09d5b.json` — question "Rank every aircraft by its worst engine's risk score...", V2, two `ok=true` attempts but `row_count: 0` on both, stored `2026-07-27T20:54:22`.
- `e651557137eefa34734a9892.json` — same question as above, V1, one `ok=true` attempt with `row_count: 0`, stored `2026-08-14T19:17:37`.

`6ad74f79...` and `e651557...` share the identical question text and both have zero-row "successful" attempts with blank `final_text` — the closest match to "two poisoned entries." But I could not confirm this pairing is what Session 3 flagged (no session-3 notes file exists anywhere in the repo — searched for `*session*` and grepped for `poison` across `.py`/`.md`/`.txt`, nothing found), and a third file (`49375c73...`) matches a similar-but-not-identical profile. Given the instruction not to guess, I left all three untouched.

### `agent/llm.py` caching error responses

**ALREADY DONE.** Both providers guard the cache write:

- `agent/llm.py:217-220` (GeminiProvider):
  ```python
  # Only successful runs are cacheable. Caching an error replays it
  # forever on a key that will never miss again.
  if run.error is None:
      _cache_store(key, run, system_prompt)
  ```
- `agent/llm.py:450-451` (GroqProvider):
  ```python
  if run.error is None:
      _cache_store(key, run, system_prompt)
  ```

Confirmed empirically too: scanning all 22 files in `.agent_cache/*.json` for a non-null `"error"` field returned zero matches.

### 13s pacing constant

**NOT obsolete — still the live default path.** `agent/llm.py:34`:

```python
RPM_SLEEP_S = 13            # measured 5 RPM free-tier ceiling (429 quotaValue='5').
                            # 60/5 = 12s minimum; 13 for clock skew.
```

`_pace()` (`agent/llm.py:40-47`) uses it and is called from `GeminiProvider.run()` at lines 172 and 208. `scripts/17_agent_gate.py:257-259` defaults `--provider` to `"gemini"` when the flag is omitted:

```python
pname = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--provider=")),
             "gemini")
provider = PROVIDERS[pname]()
```

So unless the gate is invoked with `--provider=groq`, the Gemini path — and the 13s constant — is still what runs. This is a design decision (switch the default provider, or delete `GeminiProvider` entirely) not a mechanical fix, so it was left as-is.

---

## Task 3 — Fixes applied (mechanical only)

1. **P2 fixed.** `scripts/13_connect_test.py:18`, removed the stray `=`:
   ```diff
   -        rec = s.run("RETURN 1 AS ok, datetime() AS now =").single()
   +        rec = s.run("RETURN 1 AS ok, datetime() AS now").single()
   ```
2. **P5 fixed.** Removed the empty directory: `rmdir ./killer_query.cypher`. It was untracked, so this produces no `git status` change.

**Not fixed** (left, per instructions):
- P6 (poisoned cache entries) — ambiguous which files are "the two," see above.
- `agent/llm.py` caching — already fixed in a prior session, nothing to do.
- 13s pacing constant — not dead code; changing the default provider is a design call.

---

## Task 4 — Oracle selftest

Command: `python scripts/18_oracle_selftest.py` (run from repo root, venv active)

```
[ok ] correct answer                                       want=PASS     got=PASS     attempt 0 row carries all of ['AG101', 'G-AGSA', 1.010777147894676]
[ok ] THE SESSION 3 FALSE POSITIVE - values present, wrong pairing want=FAIL     got=FAIL     trap value(s) in final attempt rows: ['AG103', 'D-AGSC']
[ok ] CO-OCCURRENCE, trap-free: golden values scattered across rows in ONE query want=FAIL     got=FAIL     attempt 0 returned all golden values but never in one row - wrong pair
[ok ] OPTION A: trap in exploratory attempt, filtered out of final - must PASS want=PASS     got=PASS     attempt 1 row carries all of ['AG101', 'G-AGSA', 1.010777147894676]
[ok ] OPTION A: trap survives into final attempt - must FAIL want=FAIL     got=FAIL     trap value(s) in final attempt rows: ['AG103']
[ok ] reversed direction - valid query, 0 rows             want=FAIL     got=FAIL     query executed but returned 0 rows - this is the silent-refusal failur
[ok ] trap flight surfaces                                 want=FAIL     got=FAIL     trap value(s) in final attempt rows: ['AG103']
[ok ] near-miss spare offered                              want=FAIL     got=FAIL     trap value(s) in final attempt rows: ['G-AGSB']
[ok ] split across two queries - not a pass, needs eyes    want=SPLIT    got=SPLIT    golden values split across attempts, none co-occurring - inspect: [(0,
[ok ] column names differ - must not matter                want=PASS     got=PASS     attempt 0 row carries all of ['AG101', 'G-AGSA', 1.010777147894676]
[ok ] float formatted as string                            want=PASS     got=PASS     attempt 0 row carries all of ['AG101', 'G-AGSA', 1.010777147894676]
[ok ] API never reached                                    want=ERROR    got=ERROR    no verdict possible: ResourceExhausted: 429

ORACLE SELFTEST PASS
```

12 of 12 lines show `[ok ]`, final line reads `ORACLE SELFTEST PASS`.

---

## Task 5 — Neo4j connectivity + DB pipeline

### Connectivity check first

Command: `python scripts/13_connect_test.py` (post-P2-fix version, run from `scripts/`, venv active)

```
uri: neo4j+s://REDACTED-INSTANCE.databases.neo4j.io
ok: 1 | server time: 2026-08-15T05:35:56.600000000+00:00
existing nodes: 38
```

Exit code 0. DB reachable — proceeded with the pipeline.

### `python scripts/14_ingest.py` (run from repo root)

```
nodes: 38
edges: 42
```

Exit code 0.

### `python scripts/15_gate.py`

```
  Airport          6
  MaintenanceHub   3
  Aircraft         8
  Engine           16
  FlightRoute      5
  INSTALLED_ON     16
  LOCATED_AT       8
  ASSIGNED_TO      5
  DEPARTS_FROM     5
  ARRIVES_AT       5
  SITUATED_AT      3
  ready_at type    DateTime  2026-06-15T13:25:00.000000000+00:00
  departure type   DateTime  2026-06-15T14:30:00.000000000+00:00
  near-miss        G-AGSA feasible=True  G-AGSB feasible=False
  eng 24 0.425053 Critical | EHAM 2.378
GATE PASS
```

Exit code 0.

### `python scripts/16_query_gate.py`

```
  1-4 baseline             AG101 / G-AGSA / eng 24 / 1.010777
  5 refusal              0 rows
  restore verified         AG101 / G-AGSA / eng 24 / 1.010777
  sabotage: no filter    AG103 wins at 1.1332
  sabotage: clock +10m   2 rows (G-AGSB qualifies)
QUERY GATE PASS
```

Exit code 0.

No verdict is offered here on what any of this output means — pasted as instructed.

---

## Could not verify

- **Which two cache files are "the two poisoned transcript entries."** No session-3 notes exist anywhere in the repo (`find . -iname "*session*"` and `grep -ri poison` both came up empty). Three candidate files were found matching a "cached success with an empty/non-answer transcript" profile; only two of the three share an identical question. Left all three untouched rather than guess.
- Whether the `13s` pacing constant / `GeminiProvider` is intended to stay as the default, or whether the intent (implied by the Groq-switch comment block at `agent/llm.py:227-238`) was for Groq to become the default provider and Gemini to be retired. Left as a design question.
- Whether `scripts/19_groq_probe.py` and `scripts/20_groq_tool_probe.py` (untracked, present since before this session started) are finished work-in-progress or scratch files — not touched, out of scope for this task list.

## Questions for Arnav

1. **P6**: which two `.agent_cache/*.json` files did you mean? My best guess, with the caveat that it's a guess: `6ad74f798ed07a4275d09d5b.json` and `e651557137eefa34734a9892.json` (same question, both "successful" zero-row/blank-answer runs). `49375c73230d4a102ce46e42.json` is a third file with a similar defect profile but a different question — is that one poisoned too, or something else entirely? None were deleted pending your confirmation.
2. The 13s-pacing/Gemini-default triage item was listed as "likely obsolete after the Groq switch" — it isn't; `gemini` is still the CLI default in `scripts/17_agent_gate.py`. Do you want the default flipped to `groq`, or is Gemini intentionally being kept as a fallback path? Not changed, since that's a design call.
