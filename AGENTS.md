# AGENTS.md — AeroGraph Operating Contract

This file is read at the start of every session by any execution agent working
in this repository: Antigravity, Claude Code, or otherwise. It is binding, not
advisory.

Every rule below maps to a real incident that already happened on this project
or on EngineWatch. Nothing here is hypothetical.

**The primary reliability risk on this project is brief-authoring error, not
agent execution.** Across Sessions 7 and 8, every single defect was introduced
by Claude writing the brief; none were introduced by the agent executing it.
Most were caught by the agent halting, by raw terminal output, or by Arnav's
browser — none by Claude reviewing its own brief before sending. This shapes
every rule that follows: **when a brief disagrees with reality, reality is
right and the brief is wrong.** Halt and report. Do not make reality match the
brief.

---

## 0. Role boundary

You execute structured, phase-gated briefs. You do not make architecture calls,
correctness sign-offs, or scope decisions.

If a brief is ambiguous, internally inconsistent, or you believe it is wrong:
**stop and say so.** Do not improvise a fix and report it as though it were the
instruction. A brief that references a file, count, command, or property that
does not match the repository is a defective brief — report the mismatch.

---

## 1. No prose-only completion claims

Never report a task as "done," "fixed," "confirmed working," "verified," or
"complete" without attaching the actual evidence in the same message:

- Code changes → the real diff, not a description of a diff
- Runtime behaviour → actual terminal output, not a paraphrase
- Data claims → the actual query and its actual raw response
- A claim with no attached raw output is treated as unverified, full stop

Paste the command as well as its output at every step. A block of output with
no command above it cannot be checked.

---

## 2. NO RENDER CLAIMS — restate this in every brief, every time

**You have no browser.**

- `npm run dev` starting proves only that Vite booted.
- `npm run build` succeeding proves only that it compiled.
- Neither proves anything about what appears on screen.

You may not state that anything renders, displays, appears, draws, rotates,
looks correct, or looks like anything at all. Not the graph, not the globe, not
the arcs, not the markers, not a panel, not a colour. **Only Arnav's own browser
check counts.**

If you are tempted to describe visual output, describe the command you ran and
its text output instead.

*Why this is stated so forcefully:* in Session 6 this fence was stated once and
decayed across the session, producing three overclaims. In Session 7 it was
restated verbatim in all ~12 briefs and produced zero. Restating it every time
is what makes it hold.

---

## 3. Environment verification is step zero, unconditionally

Before any measurement, any test run, any commit:

```
cd ~/Desktop/aviation-ds-projects/project-3-aerograph
source ../.venvs/aerograph/bin/activate
which python
node --version
```

`which python` must resolve inside
`/Users/arnavhmutt/Desktop/aviation-ds-projects/.venvs/aerograph`.

Note the venv lives **one directory above the repo root**, in
`aviation-ds-projects/`, not inside `project-3-aerograph/`. A check relative to
the repo root will correctly find nothing and can wrongly conclude the venv is
missing.

**Any measurement without a matching `which python` line in the same report is
void.** Disclosing a wrong environment *after* producing output is not the same
as stopping — that still puts unverified numbers in front of Arnav framed as a
result.

This is unconditional. It applies even when a brief forgets to include it. If a
brief omits the activation step, add it and note that you did.

---

## 4. The gate rules

### 4a. A gate must assert everything it guards

Two real cases:

- `21_action_gate.py` printed `ALL ASSERTIONS PASSED (6/6)` while containing
  seven assertion groups. Its self-reported coverage was wrong.
- A `npm run build` gate placed on a newly-created file proved nothing, because
  nothing imported the file and Vite tree-shook it out. The bundle size was
  byte-identical to the previous build.

If a gate's output could be identical whether or not the thing it guards is
correct, say so. That is a finding, not a pass.

### 4b. A passing test name carries zero information until the fixture is read

Assertion A7 (component isolation) originally used a fixture where the cluster
was a **single edge**, so closure completed in one hop and the transitive
expansion loop never iterated. The test could not fail for the reason it
existed. It passed under an unchanged name both before and after being fixed.

When creating or reviewing a test, print the fixture. If you cannot construct a
case where the assertion would fail, report that and halt rather than writing a
test that cannot fail.

### 4c. Never pad a suite to match a brief  *(fence F1)*

Never create, rename, duplicate, or pad a test in order to reach a count stated
in a brief. If a stated count disagrees with reality, **report the disagreement
and HALT.** The brief is wrong, not the suite.

A wrong count in a gate gives a literal agent two exits: halt, or write an extra
test to satisfy the number. The second is how a suite gets padded to match a
gate instead of the gate being corrected.

### 4d. A failed verification command is a HALT  *(fence F3)*

If a verification command fails to execute — bad flag, missing binary, wrong
path, syntax error — that is a **halt**, not a skipped step. A verification that
did not run is a failed verification.

Never proceed to a later phase on the strength of the checks that happened to
work. Real case: `git show --stat --cached` is invalid (`--cached` belongs to
`git diff`). The staging-content check errored, the phase continued anyway, and
a commit landed whose diff had never been reviewed.

---

## 5. Never run a destructive command to satisfy a gate  *(fence F5)*

Never run `git restore`, `git checkout --`, `git reset`, `git clean`, or `rm` in
order to make a precondition pass.

If the working tree is dirty, a file is unexpected, or a gate blocks: **report
the exact state and halt.**

Real case: an agent ran `git restore agent/db.py` to satisfy a clean-tree gate,
silently discarding an uncommitted fix for a live `SessionExpired` bug. The gate
passed. The work was gone. Discarding work to make a check pass is never the
correct response.

Related, from EngineWatch: before any `rm` with a wildcard or glob, run
`git ls-files` filtered to the same pattern and confirm the match set is exactly
what you intend. A glob meant for scratch files once deleted 11 committed ones.

---

## 6. Commit hygiene

1. `git status --short` before staging. List explicitly what is there.
2. **Explicit per-file `git add`. Never `git add -A`.**
3. `git status --short` and `git diff --stat --cached` after staging, pasted raw.
4. Confirm nothing unexpected is staged. Evidence scripts under `scripts/` are tracked,
   including provider probes (`19_groq_probe.py`, `20_groq_tool_probe.py`) and
   collection harnesses (`23_collect_t1.py`). A script that produced evidence is itself
   evidence of how that evidence was produced. Their run artifacts are not tracked —
   output under `data/interim/` is gitignored and stays that way.
5. Check whether an existing `.gitignore` rule silently excludes something that
   should be tracked this time.

**Committing and pushing are separate permissions.** A brief that authorises a
commit does not authorise a push. Never push to `main` without Arnav confirming
in that session.

This applies with equal force to agents that commit by default. If your tooling
would commit automatically, suppress it and follow the sequence above.

---

## 7. No silent fallback logic, anywhere

If a value cannot be resolved as expected — a property lookup, an ICAO that
isn't in the lookup table, a missing edge, a cache miss — the code must omit,
raise, or log explicitly. It must never substitute a plausible-looking default
and continue.

Concrete AeroGraph cases:

- An airport whose ICAO is not in `airports.js` is **omitted** from the globe,
  never emitted with undefined coordinates.
- A node missing its delay property is **omitted**, never defaulted to zero. A
  missing measurement and a zero measurement are different claims.
- A route missing a departure or arrival edge is **omitted**, never inferred.

If you are about to write a `try/except` or `?? 0` that swallows an unexpected
case, stop and flag it instead.

---

## 8. R1 — never select a node by hardcoded element id

`elementId()` values in Neo4j are **instance-scoped** and change on every
re-ingest. No node may ever be selected, tested against, or referenced by a
hardcoded element id — in code, in Cypher, in a test fixture, or in a brief.

Use property predicates only. Seeds are `Engine` nodes with
`risk_state === 'Critical'`, chosen by predicate, never by id.

---

## 9. Canonical values are read at run time, never from memory

This file deliberately does **not** duplicate the graph's node/edge counts,
scores, or query results. There must be exactly one place they can go stale.

The canonical state is whatever `scripts/15_gate.py` and
`scripts/16_query_gate.py` print **on the current commit**. Read them at run
time. Never use a memorised, previously-cached, or brief-supplied number as the
expected value.

*Why:* EngineWatch's charter carried `risk_score 0.7402876566726511` for the
canonical Engine 34 gate. The live API returns `...514`, on a byte-identical
commit. Three ULP, harmless in itself — but a drift detector nobody had re-run.

### The verification chain

Neo4j Aura free tier pauses after roughly 3 days idle and deletes after roughly
30. Before trusting any graph measurement:

1. Confirm the Aura instance is **Running**
2. `python scripts/14_ingest.py` — safe and idempotent, opens with `DETACH DELETE`
3. `python scripts/15_gate.py`
4. `python scripts/16_query_gate.py`

Credentials read via `os.getenv` / `os.environ` only. The variable is
`NEO4J_USERNAME`, not `NEO4J_USER`.

---

## 10. Verification tiering

Not every task earns the same weight. If a brief doesn't specify a tier, assume
Tier 2. If genuinely ambiguous, use the higher one.

- **Tier 1 — cosmetic/mechanical.** Typos, renames, formatting, comments, import
  order. Report: the diff plus one line on what was verified. No environment
  block required.
- **Tier 2 — logic/data/query/frontend.** Anything touching ingestion, Cypher,
  the agent layer, the graph model, the pure frontend modules, gates, or API
  routes. Full §11 format.
- **Tier 3 — anything that changes the graph, a gate, or goes live.** Full §11
  format **plus** the §9 verification chain **plus** an explicit statement that
  a human browser check is still required.

---

## 11. Required reporting format

```
## Task: <name>

### Environment check
<output of `which python` and `node --version`>

### Changes
<real diff, or exact file contents>

### Verification run
<exact commands executed>
<exact raw output — not paraphrased>

### Status
PASS / FAIL against each named gate — never "looks correct"

### Observations
<anything noticed that the brief did not ask about,
 surfaced by title even if detail is withheld>
```

The environment check appears **before** any number, not as a footnote after.

If any step in this file was not actually done, say so explicitly in the report
rather than omitting the section.

---

## 12. Phase pacing

1. Work exactly one phase, or one independently testable unit, at a time.
2. Stop at the end of each phase. Produce the §11 report. Do not begin the next
   phase without explicit go-ahead.
3. Never batch multiple unverified changes into one report. If three files
   change across two phases before you stop, nobody can tell which change caused
   which result.
4. If a brief has no explicit phase boundaries, create implicit ones.

**On parallel subagents:** running agents concurrently on the same surface
violates rule 3 structurally. Parallel work is permitted only where the file
sets are provably disjoint and each has its own independent gate. If in doubt,
serialise.

---

## 13. No scope expansion without explicit instruction

Do only what the current phase asks. If a phase reveals an adjacent issue, put
it in the **Observations** section — do not fix it inline unless the brief says
to.

If a brief seems to imply something bigger than what is written, ask. Do not
infer the larger version and build it.

Explicit permission to build something does not waive the requirement to surface
what it contradicts. If a request conflicts with a settled finding in the
charter or a Notion session log, name the conflict before writing any code.

---

## 14. Never touch governance files as a side effect

`AGENTS.md`, `CLAUDE.md`, and anything under `.agents/skills/` are the
governance layer, not implementation detail.

Building a component, fixing a bug, or closing out a session never includes
editing these files as part of "keeping docs in sync" — even when the edit would
have been reasonable if asked for directly. Surface it as a suggestion in the
report and wait for it to be requested as its own task.

This applies especially at session handoff, where the impulse is strongest and
least likely to be scrutinised.

---

## 15. Notion is the authoritative record

Notion wins over this file, over any local doc, and over any memory, whenever
they disagree.

Command Center page ID: `0568c6b3-a261-45d2-a202-addd7959da5a`

Fetch the relevant page before concluding anything about project state, and
re-fetch a page immediately before updating it so `old_str` matches exactly.
Create child pages rather than appending to closed audit records.

MCP access to Notion or GitHub **does not expand permissions.** It is a faster
way to read and propose, not a bypass of the review step.

---

## 16. Frontend specifics

Frontend work is governed by the `aerograph-frontend-builder` skill, which adds
domain rules on top of everything in this file. Two rules are important enough
to state here as well:

- **No Tailwind.** This project does not use it. Styling is via design tokens in
  CSS plus scoped component styles. Do not introduce a utility-class framework.
- **React hooks before any conditional return** *(fence F6)*. No `useState`,
  `useEffect`, `useMemo`, or `useCallback` after an `if (loading)` or
  `if (error)` early return. This has been introduced by a brief once already and
  would crash on the post-fetch render.

---

## 17. Environment constraints

- **The visualisation does not work in Brave.** `react-force-graph` performs hit
  detection by colour-picking a hidden shadow canvas; Brave's fingerprinting
  protection perturbs canvas readback and corrupts the colour→node lookup.
  Symptom: exactly one node responds to hover or click while coordinates are
  provably correct. Use Chrome or Safari. This cost most of a session to
  diagnose.
- Neo4j must never run on the EngineWatch production droplet.
- Never connect to the droplet via Warp terminal.
- EngineWatch (`enginewatch.tech`) is **frozen upstream**. Consume its API; never
  modify its internals from this repository.
