# AeroGraph

A Neo4j knowledge graph that links per-engine health predictions to airport delay
risk, so that a degrading engine can be caught **before** it strands an aircraft at
a congested airport.

> **Status: MVP complete.** The graph, the ingestion pipeline, the hand-verified
> decision query, the LLM tool binding and the graph visualisation all run
> end-to-end. Free-form LLM Cypher generation does **not** reliably work — that is
> a recorded negative result, see [Findings](#findings). Nothing in this README
> describes a capability that has not been run.
>
> Last full verification: `15_gate.py` and `16_query_gate.py` both PASS,
> reproduced 2026-08-28.

---

## The problem

Maintenance teams know which engines are degrading. Dispatch teams know which
airports are congested. In most airlines these two systems do not talk to each
other in real time, so a marginal engine gets assigned to a route into an airport
that is already delay-prone, and a recoverable maintenance event becomes an
aircraft-on-ground cascade.

AeroGraph joins the two signals in a single graph so the question _"which tail
should I swap, and why"_ can be answered by one traversal instead of two teams and
a phone call.

Conceptual reference points: Airbus Skywise (Palantir Foundry) and the
Rolls-Royce Blue Data Thread. This is a student project of far smaller scope, not
a reimplementation of either.

---

## Architecture

**Layer 1 — Micro-physics.** [EngineWatch](https://enginewatch.tech), a separate
and already-complete project, consumed here as a frozen upstream. Supplies per
engine: `rul_cycles`, `risk_score`, `risk_state`, `health_index`. Its ML internals
are out of scope for this repo.

**Layer 2 — Macro-logistics ontology.** Neo4j (AuraDB free tier). Node types:
`Engine`, `Aircraft`, `FlightRoute`, `Airport`, `MaintenanceHub`. Edges follow the
shape `(:Engine)-[:INSTALLED_ON]->(:Aircraft)-[:ASSIGNED_TO]->(:FlightRoute)`.

**Layer 3 — Agentic synthesis.** A FastAPI backend exposing a single
`execute_graph_query` tool, bound to an LLM (Gemini 2.5 Flash and Groq both
supported) with read-only guardrails.

**Interface.** A React/Vite frontend with three views: an expand-on-click force
graph, a globe plotting the six airports with their delay values, and a
side-by-side panel that runs one question against both prompt variants and shows
every Cypher string each one generated.

---

## What works, and what does not

| #   | MVP criterion                                                           | Status                                               |
| --- | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | Deterministic Mock Fleet Registry mapping engine IDs to flight profiles | Done                                                 |
| 2   | One-shot ingestion into a static Neo4j snapshot                         | Done                                                 |
| 3   | `execute_graph_query` tool bound to an LLM with guardrails              | Infrastructure done; free-form generation unreliable |
| 4   | End-to-end decision query fusing engine risk with delay risk            | Done, hand-verified                                  |
| 5   | Graph visualisation of the relevant subgraph                            | Done                                                 |
| 6   | Documented and verified end-to-end                                      | Done                                                 |

The graph holds a single-day static snapshot of **38 nodes and 42 edges** built
from FD001 engines. Two gates guard it: `15_gate.py` asserts node and edge counts,
`16_query_gate.py` asserts the decision query's result rows and runs two sabotage
controls that must change the answer.

---

## The decision query

`cypher/killer_query.cypher` is the centrepiece. Given the snapshot, it returns:

**AG101 (EGLL → EHAM)**, carrying engine 24 in `Critical` state, with an exposure
score of **1.010777**, and nominates **G-AGSA** at hub MX-LHR as the replacement
tail.

The result is guarded by two sabotage controls, both asserted by
`16_query_gate.py`:

- Remove the `risk_state = 'Critical'` filter and **AG103 wins instead**, at
  1.1332. The filter is load-bearing, not decorative.
- Loosen the readiness clock by ten minutes and **G-AGSB qualifies**, adding a
  second row. The near-miss spare is a deliberate trap in the fixture data.

The answer is also non-obvious in the right way: AG101 does not carry the sickest
engine in the fleet. It wins because its destination, EHAM, carries the highest
weather-delay figure in the snapshot (2.378) and offers no maintenance base. That
reversal of the naive engine-health ranking is the whole point of joining the two
signals.

---

## Findings

**Free-form LLM-to-Cypher generation was not reliable here.** Across four
provider × prompt-variant combinations (Gemini V1/V2, Groq V1/V2), the canonical
question has **never once** produced the correct answer, in any variant, in any
run. Seven distinct failure mechanisms were catalogued:

1. **Direction reversal** — valid Cypher, wrong arrow, zero rows, confident false
   refusal. Every detection layer reported clean.
2. **Property used as a relationship.**
3. **Hallucinated property names.**
4. **Version-mismatched syntax** — the one class the `EXPLAIN` layer caught.
5. **Under-constrained join** — returned the right flight with the wrong spare
   (D-AGSC instead of G-AGSA). The most dangerous of the seven: valid Cypher,
   nothing rejected, a fluent answer carrying real times and real hub codes. Only
   comparing the returned value against the known answer catches it.
6. **Dropped dimension** — the delay axis silently disappeared from the query and
   the model ranked on engine risk alone, answering a simpler question than the
   one asked.
7. **Direction reversal, repeated on retry** — zero rows twice, from which the
   model concluded that no flights are assigned to any aircraft with a critical
   engine. Confident, fluent, and entirely false.

The structural reason: the model reads a _description_ of the schema, never the
schema itself. So an empty result from a malformed query is indistinguishable
from an empty result from a correct query that legitimately found nothing. The
model has no signal telling the two apart, and fills the gap with fluent prose.

Two secondary results:

- **`EXPLAIN` is a weak mitigation.** It produced a notification on only 1 of 6
  distinct generated queries. It was demoted from the mitigation list rather than
  reported as a fix. One untested lead survived: the reversed-direction query's
  planner estimated zero rows _before_ execution.
- **Syntactic correctness and honesty are separate axes.** A Neo4j 5 dialect fix
  improved generated Cypher but made model self-reporting worse — a previously
  rejected query had produced an honest tool-failure report, while the newly valid
  query returned zero rows and produced a confident false statement.

This is a negative result, documented as one. It is the motivation for moving to
constrained, template-based query generation — the typed-ontology-action pattern
Palantir Foundry uses — rather than an obstacle discovered afterwards. That work
is scaffolded (`cypher/actions/`, `agent/catalog.py`, `scripts/21_action_gate.py`)
but not wired into the live agent path, and this README does not claim otherwise.

---

## The visualisation

Two views, both built to resist hairballing rather than to render everything at
once.

**Force graph.** Opens at four nodes — the two `Critical` engines and their
aircraft — and expands by neighbour ring on each click. It stalls permanently at
31 of 38 nodes. That is correct: seven Scandinavian nodes form a disconnected
component that no click path can reach. The counter never completes, and the
constraint demonstrates itself through the interface with no narration needed.
There is deliberately no "show all" control.

**Globe.** Plots the six airports with country outlines from `world-atlas`
TopoJSON, on a continuous single-hue delay ramp. The ramp is continuous rather
than banded because EUROCONTROL publishes no per-airport ATFM delay bands — a
fixed threshold would invent a standard the regulator declines to set.

> **Run the demo in Chrome or Safari, not Brave.** `react-force-graph` performs
> hit detection by colour-picking on a shadow canvas. Brave's fingerprinting
> protection perturbs canvas readback and corrupts the lookup, leaving most nodes
> unclickable.

---

## Data sources

**EUROCONTROL** `Airport_Arrival_ATFM_Delay` — public airport arrival delay data,
Europe only. Used for per-airport delay risk. The node property is weather delay
specifically (`DLY_APT_ARR_W_1`), not all-cause ATFM delay. US DOT data is a later
iteration and is not in this snapshot.

**NASA C-MAPSS (FD001)** via EngineWatch — turbofan degradation simulation data.
Engine IDs in C-MAPSS are anonymous integers with no connection to any real
aircraft.

**Mock Fleet Registry — synthetic, and deliberately so.** C-MAPSS engine IDs do
not map to real tail numbers, so this project defines a deterministic registry
assigning single-regime engines to short-haul routes and multi-regime engines to
long-haul routes. This is the entity-resolution bridge that makes the graph
possible, and it is a modelled join, not observed data. **No real airline, tail
number, or flight assignment appears anywhere in this repository.**

---

## Running it

Requires Python 3.12, Node 22, and a Neo4j AuraDB instance.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` (gitignored) with:

```
NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
GEMINI_API_KEY=<optional>
GROQ_API_KEY=<optional>
```

Build and verify the graph:

```bash
python scripts/13_connect_test.py     # verify connectivity
python scripts/14_ingest.py           # build the snapshot
python scripts/15_gate.py             # assert node and edge counts
python scripts/16_query_gate.py       # assert the decision query result
```

`14_ingest.py` opens with `DETACH DELETE`, so re-running it is safe and
idempotent. On the AuraDB free tier the instance pauses after roughly three days
idle; a paused instance fails DNS resolution, which looks identical to a deleted
one from the client. Check the Aura console before concluding anything.

Start the backend:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Start the frontend:

```bash
cd frontend && npm install && npm run dev
```

The agent gate requires an explicit provider — there is no default, so that every
run records its own provenance:

```bash
python scripts/17_agent_gate.py --provider=groq
```

---

## Repository layout

```
agent/       Neo4j driver, LLM clients, guardrails, prompt construction, action catalog
api/         FastAPI backend exposing the execute_graph_query tool
cypher/      The hand-written decision query, and action templates
data/        Mock Fleet Registry and the derived engine roster
docs/        Captured evidence: generated Cypher, EXPLAIN plans, session reports
frontend/    React/Vite interface: force graph, globe, side-by-side agent panel
scripts/     Numbered pipeline: conversion, ingestion, gates, oracle self-test
```

`.agent_cache_quarantine/` holds three cache entries isolated during a caching
defect investigation. They are tracked deliberately rather than deleted, as the
surviving evidence of that defect.

---

## On verification

Every numeric or behavioural claim in this repository was produced by running
something, not by reading code. The gates exist because an earlier project in this
series carried a wrong performance figure for two months on code-reading alone.
Where a result is negative, it is recorded as a negative result rather than
quietly dropped.

Two conventions follow from that:

- **A gate must assert what it guards.** A build gate was once placed on a file
  nothing imported; the bundler tree-shook it and the build stayed byte-identical,
  so "build clean" proved nothing. Gates here assert node counts, edge counts, and
  the query result — not a subset.
- **A green build proves nothing about runtime shape.** Polygon colours in the
  globe view were silently `undefined` while unit tests, the production build, and
  a hex-literal grep all passed, because `globe.gl` resolves accessor props
  through a function that reads a plain string as a property name. Only opening a
  browser caught it.

`AGENTS.md` and `CLAUDE.md` carry the operating contract for AI coding agents
working in this repo; `.agents/test-prompts.md` holds ten regression prompts, each
derived from a named real incident in this project's history.

---

## Not in scope

Temporal dynamics and RUL tick-down streaming; multi-day or real-time simulation;
real airline or FAA data; multi-user auth; general-purpose chat. The snapshot is
fixed at 2026-06-15 by design. Constrained query generation is the one item queued
for a deliberate second iteration.

---

## Licence and scope

Academic project. EngineWatch is a separate repository and is not vendored here.
Not affiliated with, endorsed by, or built on proprietary data from any airline,
Airbus, Rolls-Royce, EUROCONTROL, or Palantir.
