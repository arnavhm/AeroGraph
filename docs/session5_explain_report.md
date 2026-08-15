# Session 5 Overnight Report — EXPLAIN harvest

Branch: `session5/explain-harvest` (cut from `session5/mechanical`, which was itself cut from `main` at `7061c0f`; no commits on either branch).
Venv confirmed: `which python` → `/Users/arnavhmutt/Desktop/aviation-ds-projects/.venvs/aerograph/bin/python` after `source .../bin/activate`.

No commits, no `git add`, no pushes were made. Notion was not touched. The killer query, guardrails, oracle, and prompt variants were not modified — this session only ran read-only Cypher (`EXPLAIN` only, never `PROFILE`, never bare execution) and wrote three new doc files.

---

## Carried over verbatim from `docs/session5_overnight_report.md`

Per instruction, these two sections are pasted as they were written in the prior session's report, unedited, and are **not acted on** in this session.

### Could not verify

- **Which two cache files are "the two poisoned transcript entries."** No session-3 notes exist anywhere in the repo (`find . -iname "*session*"` and `grep -ri poison` both came up empty). Three candidate files were found matching a "cached success with an empty/non-answer transcript" profile; only two of the three share an identical question. Left all three untouched rather than guess.
- Whether the `13s` pacing constant / `GeminiProvider` is intended to stay as the default, or whether the intent (implied by the Groq-switch comment block at `agent/llm.py:227-238`) was for Groq to become the default provider and Gemini to be retired. Left as a design question.
- Whether `scripts/19_groq_probe.py` and `scripts/20_groq_tool_probe.py` (untracked, present since before this session started) are finished work-in-progress or scratch files — not touched, out of scope for this task list.

### Questions for Arnav

1. **P6**: which two `.agent_cache/*.json` files did you mean? My best guess, with the caveat that it's a guess: `6ad74f798ed07a4275d09d5b.json` and `e651557137eefa34734a9892.json` (same question, both "successful" zero-row/blank-answer runs). `49375c73230d4a102ce46e42.json` is a third file with a similar defect profile but a different question — is that one poisoned too, or something else entirely? None were deleted pending your confirmation.
2. The 13s-pacing/Gemini-default triage item was listed as "likely obsolete after the Groq switch" — it isn't; `gemini` is still the CLI default in `scripts/17_agent_gate.py`. Do you want the default flipped to `groq`, or is Gemini intentionally being kept as a fallback path? Not changed, since that's a design call.

---

## Task 1 — Extract Gate C generated Cypher

Full output written to `docs/gatec_generated_cypher.md`. Summary of the extraction method:

Command run (Python, via venv):
```
python3 -c "
from agent.llm import _cache_key, _cache_load
from agent.prompts import build_system_prompt
# computed _cache_key(provider, model, system_prompt, question) for every
# (provider, variant, test) combination in scripts/17_agent_gate.py's TESTS list,
# against every entry actually present in .agent_cache/
"
```

Raw result of that key computation (both providers, both variants, all 5 tests each = 20 keys checked):

```
gemini  V1 T1 canonical           key=ddbceb677517a25e581d09c9 missing
gemini  V1 T2 steer past filter   key=7af2f3813e74716e59806176 missing
gemini  V1 T3 innocent write      key=58e582953b87288447720958 missing
gemini  V1 T4 unmappable          key=b520a0bcd56955041ae7f60d missing
gemini  V1 T5 prompt injection    key=7bcb67a8c0eeeef28f67dddf missing
gemini  V2 T1 canonical           key=3fd4ebb6745e001e6483eb5e missing
gemini  V2 T2 steer past filter   key=1366e858b6166cab264432c1 missing
gemini  V2 T3 innocent write      key=cee1fb6f1cd97f01252b6313 missing
gemini  V2 T4 unmappable          key=b04057a6d7007344522d15c6 missing
gemini  V2 T5 prompt injection    key=1f4580a47cd2a8a824198790 missing
groq    V1 T1 canonical           key=c2fc304744e0534b27c61dcc FOUND
groq    V1 T2 steer past filter   key=25240a31da2794a2329862e5 FOUND
groq    V1 T3 innocent write      key=51dadb059ae23b7276ed2761 FOUND
groq    V1 T4 unmappable          key=f0b6320558927e4022b7c6ee FOUND
groq    V1 T5 prompt injection    key=11f721727646ff6f3f817747 FOUND
groq    V2 T1 canonical           key=84c08bfc08972fa397bfe037 FOUND
groq    V2 T2 steer past filter   key=a3492ac5c95bf3785422dc7a FOUND
groq    V2 T3 innocent write      key=59b89f2ac403d90edb15301c FOUND
groq    V2 T4 unmappable          key=60168b8660f12f6e842a3079 FOUND
groq    V2 T5 prompt injection    key=5e58a938a0b325d6d5b40716 FOUND
```

All 10 `groq` keys were present in `.agent_cache/`; all 10 `gemini` keys (under the current, post-fix system prompts) were absent. This is why `docs/gatec_generated_cypher.md` is built entirely from the `groq` cache entries — it is the only set of 10 that matches "all 10 tests reaching a verdict" (commit `7061c0f`).

What changed: created `docs/gatec_generated_cypher.md`. It lists, per test, the question, `run.error`, `api_calls`, and every attempt's Cypher verbatim (exact string from the cache JSON's `cypher` field), `ok`, `row_count`, `rejected_by`, `error`.

Total Cypher attempts found across all 10 tests: **6** (T3 "innocent write" and T5 "prompt injection" produced zero attempts in both variants — the model never called the query tool for those tests, per the cached transcripts).

---

## Task 2 — Neo4j connectivity check

Command: `python scripts/13_connect_test.py` (run from `scripts/`, venv active)

```
uri: neo4j+s://REDACTED-INSTANCE.databases.neo4j.io
ok: 1 | server time: 2026-08-15T05:44:30.051000000+00:00
existing nodes: 38
EXIT CODE: 0
```

DB reachable — proceeded to Task 3.

---

## Task 3 — EXPLAIN each distinct query

Full output written to `docs/gatec_explain_notifications.md`, one section per query, containing: the Cypher submitted, the EXPLAIN error (if any), the raw plan text, the raw `notifications` list (legacy driver surface, has a `code` field), and the raw `gql_status_objects` list (newer driver surface, has a `gql_status` code).

Method: `session.run("EXPLAIN " + cypher)` then `result.consume()`, reading `.plan`, `.notifications`, and `.gql_status_objects` off the `ResultSummary`. No `PROFILE`, no bare execution, anywhere in this session.

Command run:
```
python /path/to/scratchpad/run_explain.py
```

Raw stdout from that run:
```
groq/V1/T1 canonical/attempt0 error= None notifications_legacy= 0 gql_status= 1
groq/V1/T1 canonical/attempt1 error= None notifications_legacy= 0 gql_status= 1
groq/V1/T2 steer past filter/attempt0 error= None notifications_legacy= 0 gql_status= 1
groq/V2/T1 canonical/attempt0 error= None notifications_legacy= 0 gql_status= 1
groq/V2/T2 steer past filter/attempt0 error= None notifications_legacy= 0 gql_status= 1
groq/V2/T4 unmappable/attempt0 error= None notifications_legacy= 1 gql_status= 2
```

All 6 distinct Cypher strings EXPLAINed without error. Full plan text and full notification/gql_status_objects payloads for each are in `docs/gatec_explain_notifications.md` — not repeated here in full since it would just be a duplicate paste; the one query that raised a real notification (`groq/V2/T4 unmappable/attempt0`, `avg(a.fuel_efficiency)`) is reproduced below since Task 4 needs it:

```json
[
  {
    "title": "The provided property key is not in the database",
    "code": "Neo.ClientNotification.Statement.UnknownPropertyKeyWarning",
    "description": "One of the property names in your query is not available in the database, make sure you didn't misspell it or that the label is available when you run this statement in your application (the missing property name is: fuel_efficiency)",
    "severity": "WARNING",
    "category": "UNRECOGNIZED",
    "position": {
      "offset": 40,
      "line": 1,
      "column": 41
    }
  }
]
```

corresponding `gql_status_objects` entry:
```json
{
  "gql_status": "01N52",
  "status_description": "warn: property key does not exist. The property `fuel_efficiency` does not exist in database `REDACTED-INSTANCE`. Verify that the spelling is correct.",
  "raw_classification": "UNRECOGNIZED",
  "raw_severity": "WARNING",
  "position": "line: 1, column: 41, offset: 40"
}
```

Every EXPLAIN, on every query, also returns a `gql_status_objects` entry with `gql_status: "00001"`, `status_description: "note: successful completion - omitted result"`. This is present on all 6 queries and is the standard "no rows were actually produced because this was EXPLAIN" status, not a warning about the query — it is excluded from the frequency table below as noise, not as a judgment call about the query.

---

## Task 4 — Frequency table

Plain counts only. Notification source = `ResultSummary.notifications` (legacy, `code` field) checked against the four types named in the task, plus a row for anything else observed. Second table = `gql_status_objects` codes, excluding the benign `00001` completion status present on every query.

Command run:
```
python3 -c "
from collections import defaultdict
counts = defaultdict(list)
for e in data:
    for n in e['notifications_legacy']:
        counts[n['code']].append(e['label'])
    for g in e['gql_status_objects']:
        if g['gql_status'] == '00001': continue
        counts[f\"gql_status:{g['gql_status']}\"].append(e['label'])
"
```

Raw output:
```
Neo.ClientNotification.Statement.UnknownPropertyKeyWarning 1 ['groq/V2/T4 unmappable/attempt0']
gql_status:01N52 1 ['groq/V2/T4 unmappable/attempt0']
```

### Frequency table (legacy `notifications` surface)

| Notification code | Count | Queries |
|---|---|---|
| UnknownLabelWarning | 0 | — |
| UnknownRelationshipTypeWarning | 0 | — |
| UnknownPropertyKeyWarning | 1 | groq/V2/T4 unmappable/attempt0 |
| CartesianProduct | 0 | — |
| Eager (any eager-operator notification) | 0 | — |
| (any other code) | 0 | — |

### Frequency table (`gql_status_objects` surface, excluding benign `00001`)

| gql_status | Count | Queries |
|---|---|---|
| 01N52 | 1 | groq/V2/T4 unmappable/attempt0 |
| (any other non-00001 status) | 0 | — |

6 queries checked total. 5 of 6 produced zero notifications on either surface.

---

## Could not verify

- Whether the single `UnknownPropertyKeyWarning`/`01N52` notification on `groq/V2/T4 unmappable/attempt0` was also present when this query actually ran live during the Gate C run (only `EXPLAIN` was run in this session, against the current graph state; the cached transcript's `attempts[0].error` field is `null` and `row_count` is `1`, meaning the live run executed without erroring and returned a row — I did not re-run it live to confirm the notification would have fired identically at that point in time, since that would require more than EXPLAIN or would touch the same graph state during a different session).
- Whether the six distinct Cypher strings collected are the *only* ones the models produced during the Gate C run, or whether earlier exploratory attempts exist that got dropped before caching. The cache only stores the `attempts` list as it stood when `run.error is None` triggered a single `_cache_store` call — if there were intermediate provider-side retries not captured in `Attempt` objects, they are not visible from `.agent_cache` and were not collected.
- The prior report's "Could not verify" and "Questions for Arnav" items (P6 cache files, the 13s/Gemini-default design question, and the two untracked `19_groq_probe.py`/`20_groq_tool_probe.py` scripts) — carried forward above verbatim, not re-investigated or re-verified in this session per the task instructions ("Do not act on them").

## Questions for Arnav

None new for this session — the task list was mechanical extraction and EXPLAIN-only collection, and all 6 distinct queries ran cleanly under EXPLAIN with no ambiguity in which run to extract from (the cache-key computation in Task 1 made the groq-vs-gemini choice unambiguous, not a guess).
