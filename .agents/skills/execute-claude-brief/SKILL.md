---
name: execute-claude-brief
description: Use this skill whenever Arnav pastes a structured, phase-gated implementation brief authored by Claude for the AeroGraph project — briefs typically contain numbered phases, explicit stop-and-report gates, restated fences (F1/F3/F5/F6/R1), or file-level instructions. Also trigger on any multi-step change to ingestion, Cypher, the agent layer, gates, or API routes, even if it isn't labelled a brief. Do NOT use this for frontend work under frontend/ — that's the aerograph-frontend-builder skill; defer to it instead.
---

# Execute Claude Brief — AeroGraph

This skill governs **how** to work through a brief, not what the rules are. The
underlying invariants live in `AGENTS.md` at the repository root and apply
whether or not this skill is active. Read `AGENTS.md` first if you have not
already this session.

## The premise this skill exists on

On this project, **the brief is the most likely thing to be wrong.** Across two
full sessions, every defect was introduced in brief authoring; none in
execution. Most were caught by an agent halting on a mismatch.

Your halts are the primary defect-detection mechanism. Treat a disagreement
between the brief and the repository as a finding worth reporting, never as
noise to work around.

## Recognising a brief

Numbered phases; a "stop and report" or "wait for confirmation" marker; explicit
file paths with file-level instructions; a stated gate or halt condition per
step; restated fences at the top.

Claude's briefs for this project are deliberately literal. If a step seems to
require inventing an approach Claude did not specify, that is a signal to stop
and ask — not to improvise.

## Execution pacing

1. **One phase at a time.** Never batch multiple unverified changes into one
   report. If three files change across two phases before you stop, nobody can
   attribute a result to a change.
2. **Stop at every gate.** Produce the report. Wait for explicit go-ahead.
3. **If a brief has no phase boundaries, create implicit ones** — one module,
   one route, one migration step. Each gets its own report.
4. **Parallel execution is off by default.** Concurrent agents on the same
   surface break attribution structurally. Only parallelise where file sets are
   provably disjoint and each has its own gate. When in doubt, serialise.

## Gate report format

Use `AGENTS.md` §11 exactly, at the tier §10 calls for. Environment check first,
before any number. A phase is not complete without it.

"This phase is done" with no attached report is not a gate report. If you
skipped a step, say so explicitly rather than omitting the section.

## Halt conditions — non-negotiable

Halt and report, do not work around:

- `which python` does not resolve inside `.venvs/aerograph`
- A stated count, file list, or expected value disagrees with reality *(F1)*
- A verification command fails to execute *(F3)*
- The working tree is dirty or contains unexpected files — **never** clean it *(F5)*
- A brief references a node by hardcoded `elementId()` *(R1)*
- A brief asks you to claim a visual result
- A gate's output would be identical whether or not the guarded thing is correct

## Conflict handling

If anything in a brief conflicts with an `AGENTS.md` invariant — implies a
silent fallback, skips the venv check, asks for a render claim, puts coordinates
into the graph, hardcodes an element id, or requests a push — **stop and surface
the conflict as its own line.**

Do not silently follow the brief over the invariant. Do not silently follow the
invariant while ignoring what the brief asked for. Name it and let Arnav or
Claude resolve it.

This applies even when a request is explicit and clearly worded. If a prompt
comes directly from Arnav rather than through a brief, and it requires a design
decision Claude has not weighed in on — how to encode a value, how to rank
results, whether a query is valid for the data — that is not a decision this
skill may make silently just because the ask was clear. Name the choice out
loud. Flag it, or suggest routing it through Claude first.

## Ambiguity handling

If a step is genuinely underspecified — not merely harder than expected, but
actually missing information needed to proceed correctly, such as referencing a
file or property that does not match the repository — stop and ask.

This project has a documented history of plausible-sounding but wrong
assumptions passing as confirmed. Do not add to it.

## Scope discipline

Do only what the current phase asks. If a phase reveals an adjacent issue, put
it in **Observations** — do not fix it inline unless the brief says to. Scope
expansion without instruction is out of bounds per `AGENTS.md` §13.

Surface **every** observation by title, even where detail is withheld. An
observation that was noticed and not mentioned is the same as one that was
missed.
