# AeroGraph

A Neo4j knowledge graph that links per-engine health predictions to airport delay
risk, so that a degrading engine can be caught **before** it strands an aircraft at
a congested airport.

> **Status: in progress.** Demo target August 2026. The graph, the ingestion
> pipeline and the hand-verified decision query all work end-to-end. Graph
> visualisation is not built yet, and free-form LLM Cypher generation does **not**
> reliably work — see [Findings](#findings). Nothing in this README describes a
> capability that has not been run.

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

---

## What works, and what does not

| #   | MVP criterion                                                           | Status                                               |
| --- | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | Deterministic Mock Fleet Registry mapping engine IDs to flight profiles | Done                                                 |
| 2   | One-shot ingestion into a static Neo4j snapshot                         | Done                                                 |
| 3   | `execute_graph_query` tool bound to an LLM with guardrails              | Infrastructure done; free-form generation unreliable |
| 4   | End-to-end decision query fusing engine risk with delay risk            | Done, hand-verified                                  |
| 5   | Graph visualisation of the relevant subgraph                            | Not started                                          |
| 6   | Documented and verified end-to-end                                      | In progress                                          |

The graph currently holds a single-day static snapshot of **38 nodes and 42
edges** built from FD001 engines. Two gates guard it: `15_gate.py` asserts node
and edge counts, `16_query_gate.py` asserts the decision query's result rows.

---

## Findings

**Free-form LLM-to-Cypher generation was not reliable here.** Across four
provider × prompt-variant combinations (Gemini V1/V2, Groq V1/V2), none reproduced
the decision query from a natural-language question. The failures were not one
recurring bug — they were four distinct mechanisms, including reversed
relationship direction, hallucinated property names, and a confidently-worded
answer built on zero returned rows.

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
constrained, template-based query generation rather than an obstacle discovered
afterwards.

---

## Data sources

**EUROCONTROL** `Airport_Arrival_ATFM_Delay` — public airport arrival delay data,
Europe only. Used for per-airport delay risk. US DOT data is a later iteration and
is not in this snapshot.

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

Requires Python 3.12 and a Neo4j AuraDB instance.

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

Then:

```bash
python scripts/13_connect_test.py     # verify connectivity
python scripts/14_ingest.py           # build the snapshot
python scripts/15_gate.py             # assert node and edge counts
python scripts/16_query_gate.py       # assert the decision query result
```

The agent gate requires an explicit provider — there is no default, so that every
run records its own provenance:

```bash
python scripts/17_agent_gate.py --provider=groq
```

---

## Repository layout

```
agent/       Neo4j driver, LLM clients, guardrails, prompt construction
api/         FastAPI backend exposing the execute_graph_query tool
cypher/      The hand-written decision query
data/        Mock Fleet Registry and the derived engine roster
docs/        Captured evidence: generated Cypher, EXPLAIN plans, session reports
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

---

## Licence and scope

Academic project. EngineWatch is a separate repository and is not vendored here.
Not affiliated with, endorsed by, or built on proprietary data from any airline,
Airbus, Rolls-Royce, EUROCONTROL, or Palantir.
