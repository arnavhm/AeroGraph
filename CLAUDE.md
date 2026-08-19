@AGENTS.md

## Project Identity

- **Project:** AeroGraph — knowledge graph + LLM agent for pre-emptive tail swaps
- **Repo:** <https://github.com/arnavhm/AeroGraph>
- **Local:** `~/Desktop/aviation-ds-projects/project-3-aerograph`
- **Venv:** `~/Desktop/aviation-ds-projects/.venvs/aerograph` — one level *above*
  the repo root. Python 3.12, pandas 3.0.3. Node 22.
- **Graph:** Neo4j AuraDB free tier. Pauses ~3 days idle, deletes ~30.
- **Notion command center (authoritative):** `0568c6b3-a261-45d2-a202-addd7959da5a`
  — check at session start; wins over anything in this file.

## What AeroGraph is

Micro-level engine health (EngineWatch, frozen upstream) fused with macro-level
flight logistics (EUROCONTROL arrival ATFM delay) through a Neo4j knowledge
graph, so an agent can recommend a tail swap before a degrading engine triggers
a cascading AOG at a high-traffic airport.

Three layers:

1. **Micro-physics** — EngineWatch. Consumed as a black box via
   `https://enginewatch.tech/api/predict`. Per engine: `rul_cycles`,
   `risk_score`, `risk_state`, `health_index`. **Never modified from here.**
2. **Macro-logistics ontology** — Neo4j. Node types: `Engine`, `Aircraft`,
   `Airport`, `FlightRoute`, `MaintenanceHub`.
3. **Agentic synthesis** — an LLM writes or selects Cypher and returns
   natural-language decision support.

Region scope: **EUROCONTROL / Europe only.** US DOT is a later iteration.

The entity-resolution bridge between anonymous C-MAPSS engine IDs and flight
data is a **deterministic Mock Fleet Registry**. This is stated plainly as
enterprise data-integration work, never presented as real airline data.

## Where things live — read from source, don't duplicate here

- **Execution rules, gates, fences, reporting format:** `AGENTS.md` (included
  above). Binding.
- **Canonical graph state:** whatever `scripts/15_gate.py` and
  `scripts/16_query_gate.py` print on the current commit. Never memorised,
  never duplicated into a doc. See `AGENTS.md` §9.
- **Session history, decisions, corrections:** Notion. Authoritative.
- **Frontend rules:** `.agents/skills/aerograph-frontend-builder/SKILL.md`
- **Brief execution pacing:** `.agents/skills/execute-claude-brief/SKILL.md`
- **Contract regression tests:** `.agents/test-prompts.md`

This file deliberately does not restate node counts, scores, query results, or
architecture detail. EngineWatch's equivalent file drifted badly by duplicating
them — that failure mode is the reason this one is thin.

## Repository structure

> **Verify this against the actual tree before relying on it.** It is written
> from the project record, not from a filesystem read, and paths may have moved.

```
api/           # FastAPI — main.py: /health, /query, /ask
               # Caddy strips /api, so schema path /query = public /api/query
agent/         # db.py           driver + connection lifetime
               # llm.py          provider clients (Gemini, Groq)
               # prompts.py      prompt text — four parked mitigations live here
               # schema_builder.py  schema description given to the model
               # graph_tool.py   execute_graph_query tool binding
               # guardrails.py   Cypher validation / rejection
               # catalog.py      action catalog + validate_params (Option D)
cypher/
  killer_query.cypher   # criterion 4 — the tail-swap query, hand-authored
  actions/              # parameterised actions for constrained generation
scripts/       # 01–22, numbered and ordered. Load-bearing:
               #   14_ingest.py        idempotent, opens with DETACH DELETE
               #   15_gate.py          node/edge counts + temporal types
               #   16_query_gate.py    killer query + both sabotage controls
               #   17_agent_gate.py    agent run capture
               #   18_oracle_selftest.py  row-based oracle
               #   21_action_gate.py   Option D — self-reported count is WRONG,
               #                       prints 6/6 with seven assertion groups
               #   22_graph_dump.py    graph inspection
               # 19_ and 20_groq_probe are deliberately untracked.
frontend/      # Vite + React 19
  src/
    App.jsx           # fetch once, own visibleIds + viewMode, delegate
    GraphView.jsx     # ForceGraph2D, click-to-expand  (criterion 5 — CLOSED)
    GlobeView.jsx     # react-globe.gl, arcs + markers
    graphModel.js     # pure: normalizeEndpoint, buildAdjacency, seedIds, expand
    airports.js       # ICAO → {lat, lon, name}, generated from OurAirports
    routeArcs.js      # pure: routes → arc records
    airportMarkers.js # pure: airports → colour + altitude markers
    liveClosureProbe.mjs  # permanent diagnostic; .mjs so node --test skips it
    *.test.mjs        # node --test
    index.css, App.css, assets/  # Vite template scaffolding — must not ship
```

Core logic lives in `api/`, `agent/`, `cypher/`, `scripts/`, and the **pure**
frontend modules. Never in a component, never in a notebook.

## Hard constraints

- **EngineWatch is frozen.** Consume the API. Do not reopen its ML internals.
- **Coordinates never enter the graph.** Airport lat/lon lives in a frontend
  lookup keyed on ICAO. Adding it to `14_ingest.py` would force re-proving
  `15_gate.py` and `16_query_gate.py` for a presentational value.
- **No hardcoded element ids.** Property predicates only — `AGENTS.md` §8.
- **No dummy or placeholder data in any component.** Every UI state wires to a
  real backend payload, even for a quick test.
- **No real airline or FAA data.** The registry is synthetic and labelled.
- Fixed seeds for anything stochastic.

## The MVP definition of done — the anti-scope-creep anchor

AeroGraph MVP is done, and stops, when:

1. ✅ Deterministic Mock Fleet Registry maps engine IDs → flight profiles
2. ✅ One-shot ingestion populates a static Neo4j snapshot
3. ✅ One graph-query tool bound to an LLM, with Cypher guardrails *(infrastructure
   complete; free-form generation is a documented negative finding)*
4. ✅ One killer end-to-end query: natural language → Cypher → tail-swap
   recommendation fusing engine risk with airport delay
5. ✅ One graph visualisation, click-to-expand, designed against hairball-ing
6. ❌ **Documented once (Notion + README), verified end-to-end, then STOP**

Criterion 6 is the only open MVP item. Anything else currently in flight —
globe view, dashboard shell, constrained Cypher generation — is **post-MVP work
being done ahead of it, by explicit decision.** Name it as such rather than
letting it blur into the MVP.

Explicitly out of scope until there is a real trigger: temporal/streaming graph
dynamics, multiple query types, general chat, multi-day simulation, real FAA
data, auth, multi-user, anything that turns a one-query demo into a platform.

## Ownership

- **Arnav** owns every correctness decision, and owns the killer Cypher query by
  hand. Claude explains and stress-tests it; Claude does not author it.
- **Claude** owns architecture, correctness review, briefs, and diagnostic
  reasoning. Claude's briefs are the primary defect source on this project —
  see the note at the top of `AGENTS.md`.
- **Execution agents** (Antigravity, Claude Code) execute phase-gated briefs and
  halt on any mismatch. They do not make judgement calls and never perform the
  first-ever run of anything numeric unsupervised.

## Session start checklist

1. Fetch the Notion command center for current state.
2. Confirm `which python` resolves into `.venvs/aerograph`.
3. Confirm the Aura instance is Running before trusting any graph measurement.
4. If working from a Claude brief, use the `AGENTS.md` §11 report format, not a
   narrative summary.
