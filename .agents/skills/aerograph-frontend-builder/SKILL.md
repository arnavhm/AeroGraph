---
name: aerograph-frontend-builder
description: Use this whenever an execution agent is asked to implement AeroGraph frontend changes under frontend/ — the dashboard shell, GraphView, GlobeView, the agent query panel, design tokens, layout, or any brief authored for that surface. Enforces build-exactly-to-brief discipline and requires raw verification evidence before anything is reported as done. Do NOT use this for Cypher, ingestion, gates, or the agent backend — out of scope. Do NOT use this to make design or UX decisions; this skill builds what is specified and proves it compiles.
---

# AeroGraph Frontend Builder

Everything in `AGENTS.md` applies underneath this skill. This adds domain rules;
it does not replace them.

## Role & boundaries

Sole focus: implementing changes under `frontend/` exactly as specified.

Never make design or UX decisions unprompted. If a brief is ambiguous or missing
a detail needed to proceed, stop and report the specific gap. Do not guess and
do not quietly improvise a reasonable version.

Never touch Cypher, ingestion scripts, gates, or `agent/` from a frontend brief.

Voice: plain, factual, evidence-first. No narrative filler, no editorialising
about how smoothly something went.

## The one rule that matters most

**You have no browser.** "Looks right," "renders correctly," "confirmed
working," and "the globe displays" are not acceptable completion reports.
`npm run dev` starting proves Vite booted. `npm run build` succeeding proves it
compiled. Neither says anything about what appears on screen.

Every claim must be backed by something checkable: a real diff, real build
output, real test output, a real API response. See `AGENTS.md` §2 — that fence
is restated in every brief for a reason.

## Stack — what this project actually uses

- **React 19**, **Vite**, plain JavaScript (`.jsx` / `.js`, not TypeScript)
- `react-force-graph-2d` for the graph view
- `react-globe.gl` (with three.js) for the globe view
- `node --test` with `node:assert` for the pure modules
- **No Tailwind.** Do not introduce it or any other utility-class framework.
- **No CSS-in-JS libraries.**

## Styling — design tokens, not inline styles, not Tailwind

Colour, spacing, typography, and border values live as CSS custom properties in
a single tokens file. Components reference tokens; they do not hardcode values.

- Never hardcode a hex colour in a component. If a needed value has no token,
  **stop and report** rather than inventing one.
- The Vite template CSS (`--accent: #aa3bff`, `.hero`, `#next-steps`, `#spacer`,
  `.counter`, `.ticks`) is dead template scaffolding and must not ship.
- `layout.css` currently depends on CSS load order. If layout breaks after
  `npm run build` but holds in dev, that is the cause — report it, do not paper
  over it with `!important`.

## Semantic colour — locked, from charter §14

This came from real user feedback, not self-set taste. It is not negotiable.

- **Red** — risk only
- **Amber** — caution only
- **Green** — healthy only
- **One neutral accent (cyan)** — all chrome, grid, borders, labels, inactive
  states, and non-status telemetry
- **No other saturated hue.** No magenta, no purple, no multi-hue heat ramps
  passing through yellow or green.

Consequences in practice:

- Engine `risk_state` is the only semantic use of colour in the graph view.
  Everything non-Engine is neutral.
- The airport delay ramp stays inside a single red hue, varying saturation and
  lightness only.
- **A UI control never carries a semantic colour.** A toggle, button, or tab
  must never be red, amber, or green.

Plain language leads; the technical term is a smaller secondary label. Tooltips
add depth, never basic meaning.

## Hard rules

1. **No dummy or placeholder data, ever.** Every UI state wires to a real
   backend payload, even for a quick test or a shape preview. If a payload shape
   is unclear, call the endpoint and read the actual response before writing the
   component.
2. **No silent fallback.** If a prop, endpoint, or data shape is not what is
   expected, fail loud — omit the item and log, or show a visible error state.
   Never substitute a plausible default. An unknown ICAO is omitted, not
   defaulted; a missing delay value is omitted, not zeroed.
3. **Hooks before conditional returns** *(F6)*. No `useState`, `useEffect`,
   `useMemo`, or `useCallback` after an `if (loading)` or `if (error)` early
   return.
4. **Pure modules stay pure.** `graphModel.js`, `airports.js`, `routeArcs.js`,
   and `airportMarkers.js` have zero React, DOM, or fetch imports. Never add
   one. Components consume these modules; they never reimplement or duplicate
   their logic, and never compute a coordinate, colour, or normalisation
   locally.
5. **Fetch once.** Graph data is fetched at the top level and passed down. Never
   refetch per view or on toggle.
6. **Bundle reality.** The bundle is over 2 MB because three.js is in it — that
   is expected and accepted for this project, not a defect to fix. Do not add
   further heavy dependencies without the brief saying so, and do not
   "optimise" with code-splitting unless asked.
7. **Reuse over rebuild.** Existing components: `App`, `GraphView`, `GlobeView`.
   Existing pure modules as listed above. Do not recreate, rename, or
   restructure any of them unless the brief explicitly asks.
8. **No unrequested controls.** No "show all" button on the graph — expansion
   stalling at 31 of 38 is a deliberate demonstration of the disconnected
   component, and a show-all control would destroy it. No auto-rotation, no
   legend, no animation unless specified.

## Verification for every frontend change

```
which python && node --version
cd frontend && node --test src/*.test.mjs
cd frontend && npm run build
```

Then check, and state explicitly:

- Did any **pre-existing** assertion fail? Any failure is a halt.
- Did the bundle size change in the direction you expect? If a brief adds code
  and the bundle is unchanged, **the code is not in the build** — report that as
  a finding, do not report the build as clean.
- Are any hardcoded colours present in the diff? Grep for `#` in changed
  component files.

Close every frontend report with the statement that a human browser check by
Arnav is still required before the change is considered done.

## Reporting

`AGENTS.md` §11 format. Environment check first. Real diff, real command output,
PASS/FAIL against each named gate, then Observations — every observation
surfaced by title, even where detail is withheld.
