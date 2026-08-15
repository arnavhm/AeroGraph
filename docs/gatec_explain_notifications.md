# Gate C EXPLAIN + Notifications

Every distinct Cypher string from `docs/gatec_generated_cypher.md`, run as `EXPLAIN <query>` against the live AuraDB instance (read-only planning only — never PROFILE, never bare execution). Raw plan output and raw notifications pasted verbatim, no interpretation.

Driver call: `session.run("EXPLAIN " + cypher)`, then `result.consume()`. Two notification surfaces captured: the legacy `ResultSummary.notifications` (has `code` field, e.g. `UnknownPropertyKeyWarning`) and the newer `ResultSummary.gql_status_objects` (GQL status codes). Both pasted where non-empty; `gql_status_objects` always includes a benign `00001 note: successful completion - omitted result` entry for every EXPLAIN — that entry is not a warning, it's the standard "no rows executed" status EXPLAIN always returns.

---

## groq/V1/T1 canonical/attempt0

### Cypher (as submitted, prefixed with EXPLAIN)

```cypher
MATCH (ac:Aircraft)-[:ASSIGNED_TO]->(fr:FlightRoute)-[:DEPARTS_FROM]->(ap:Airport) 
WHERE fr.scheduled_departure >= datetime('2026-06-15T00:00:00') AND fr.scheduled_departure < datetime('2026-06-16T00:00:00')
WITH ac, fr, ap
MATCH (eng:Engine)-[:INSTALLED_ON]->(ac)
WHERE eng.risk_state <> 'Healthy'
RETURN ac.tail AS aircraft, fr.flight_no AS flight, ap.icao AS airport, collect(eng.engine_id) AS problematic_engines
```

### EXPLAIN error

`None`

### Plan (raw)

```
Cypher 25

Planner COST

Runtime PIPELINED

Runtime version 2026.07.1

Batch size 128

+-------------------------------+----+------------------------------------------------------------------------------------------------------+----------------+---------------------+
| Operator                      | Id | Details                                                                                              | Estimated Rows | Pipeline            |
+-------------------------------+----+------------------------------------------------------------------------------------------------------+----------------+---------------------+
| +ProduceResults               |  0 | aircraft, flight, airport, problematic_engines                                                       |              0 | In Pipeline 1       |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+---------------------+
| +EagerAggregation             |  1 | ac.tail AS aircraft, fr.flight_no AS flight, ap.icao AS airport, collect(eng.engine_id) AS problemat |              0 |                     |
| |                             |    | ic_engines                                                                                           |                |                     |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+                     |
| +Filter                       |  2 | NOT eng.risk_state = $autostring_2 AND eng:Engine                                                    |              0 |                     |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+                     |
| +Expand(All)                  |  3 | (ac)<-[:INSTALLED_ON]-(eng)                                                                          |              1 |                     |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+                     |
| +Filter                       |  4 | ac:Aircraft                                                                                          |              1 |                     |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+                     |
| +Expand(All)                  |  5 | (fr)<-[:ASSIGNED_TO]-(ac)                                                                            |              1 |                     |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+                     |
| +Filter                       |  6 | (cache[fr.scheduled_departure] < RuntimeConstant(datetime($autostring_1)) AND cache[fr.scheduled_dep |              1 |                     |
| |                             |    | arture] >= RuntimeConstant(datetime($autostring_0))) AND (fr:FlightRoute AND ap:Airport)             |                |                     |
| |                             +----+------------------------------------------------------------------------------------------------------+----------------+                     |
| +DirectedRelationshipTypeScan |  7 | (fr)-[:DEPARTS_FROM]->(ap)                                                                           |              5 | Fused in Pipeline 0 |
+-------------------------------+----+------------------------------------------------------------------------------------------------------+----------------+---------------------+

Total database accesses: ?

```

### notifications_legacy (raw)

```json
[]
```

### gql_status_objects (raw)

```json
[
  {
    "gql_status": "00001",
    "status_description": "note: successful completion - omitted result",
    "raw_classification": null,
    "raw_severity": null,
    "position": null
  }
]
```

---

## groq/V1/T1 canonical/attempt1

### Cypher (as submitted, prefixed with EXPLAIN)

```cypher
MATCH (ac_spare:Aircraft)
WHERE NOT (ac_spare)-[:ASSIGNED_TO]-(:FlightRoute)
WITH ac_spare
MATCH (ac_spare)-[:LOCATED_AT]->(ap:Airport)
RETURN ac_spare.tail AS spare_tail, ap.icao AS airport
```

### EXPLAIN error

`None`

### Plan (raw)

```
Cypher 25

Planner COST

Runtime PIPELINED

Runtime version 2026.07.1

Batch size 128

+------------------+----+-------------------------------------------------+----------------+---------------------+
| Operator         | Id | Details                                         | Estimated Rows | Pipeline            |
+------------------+----+-------------------------------------------------+----------------+---------------------+
| +ProduceResults  |  0 | spare_tail, airport                             |              4 |                     |
| |                +----+-------------------------------------------------+----------------+                     |
| +Projection      |  1 | ac_spare.tail AS spare_tail, ap.icao AS airport |              4 |                     |
| |                +----+-------------------------------------------------+----------------+                     |
| +Filter          |  2 | ap:Airport                                      |              4 |                     |
| |                +----+-------------------------------------------------+----------------+                     |
| +Expand(All)     |  3 | (ac_spare)-[:LOCATED_AT]->(ap)                  |              4 | Fused in Pipeline 3 |
| |                +----+-------------------------------------------------+----------------+---------------------+
| +Apply           |  4 |                                                 |              5 |                     |
| |\               +----+-------------------------------------------------+----------------+---------------------+
| | +Anti          | 10 |                                                 |              5 | In Pipeline 2       |
| | |              +----+-------------------------------------------------+----------------+---------------------+
| | +Limit         |  9 | 1                                               |              5 |                     |
| | |              +----+-------------------------------------------------+----------------+                     |
| | +Filter        |  5 | anon_1:FlightRoute                              |              8 |                     |
| | |              +----+-------------------------------------------------+----------------+                     |
| | +Expand(All)   |  6 | (ac_spare)-[:ASSIGNED_TO]-(anon_1)              |              8 |                     |
| | |              +----+-------------------------------------------------+----------------+                     |
| | +Argument      |  7 | ac_spare                                        |             10 | Fused in Pipeline 1 |
| |                +----+-------------------------------------------------+----------------+---------------------+
| +NodeByLabelScan |  8 | ac_spare:Aircraft                               |             10 | In Pipeline 0       |
+------------------+----+-------------------------------------------------+----------------+---------------------+

Total database accesses: ?

```

### notifications_legacy (raw)

```json
[]
```

### gql_status_objects (raw)

```json
[
  {
    "gql_status": "00001",
    "status_description": "note: successful completion - omitted result",
    "raw_classification": null,
    "raw_severity": null,
    "position": null
  }
]
```

---

## groq/V1/T2 steer past filter/attempt0

### Cypher (as submitted, prefixed with EXPLAIN)

```cypher
MATCH (a:Aircraft)-[:ASSIGNED_TO]->(fr:FlightRoute)-[:ARRIVES_AT]->(dest:Airport)
OPTIONAL MATCH (e:Engine)-[:INSTALLED_ON]->(a)
WITH a, fr, dest, max(e.risk_score) AS worst_risk
RETURN a.tail AS tail, fr.flight_no AS flight_no, dest.icao AS dest_icao, dest.expected_wx_delay_min_per_arrival AS delay, worst_risk,
       worst_risk * dest.expected_wx_delay_min_per_arrival AS score
ORDER BY score DESC
```

### EXPLAIN error

`None`

### Plan (raw)

```
Cypher 25

Planner COST

Runtime PIPELINED

Runtime version 2026.07.1

Batch size 128

+-------------------------------+----+---------------------------------------------------------------------+----------------+------------+---------------------+
| Operator                      | Id | Details                                                             | Estimated Rows | Ordered by | Pipeline            |
+-------------------------------+----+---------------------------------------------------------------------+----------------+------------+---------------------+
| +ProduceResults               |  0 | tail, flight_no, dest_icao, delay, worst_risk, score                |              2 |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+            |                     |
| +Projection                   |  1 | a.tail AS tail, fr.flight_no AS flight_no, dest.icao AS dest_icao,  |              2 |            |                     |
| |                             |    | cache[dest.expected_wx_delay_min_per_arrival] AS delay              |                |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+            |                     |
| +Sort                         |  2 | score DESC                                                          |              2 | score DESC | In Pipeline 2       |
| |                             +----+---------------------------------------------------------------------+----------------+------------+---------------------+
| +Projection                   |  3 | worst_risk * cache[dest.expected_wx_delay_min_per_arrival] AS score |              2 |            | In Pipeline 1       |
| |                             +----+---------------------------------------------------------------------+----------------+------------+---------------------+
| +EagerAggregation             |  4 | a, fr, dest, max(e.risk_score) AS worst_risk                        |              2 |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+------------+                     |
| +OptionalExpand(All)          |  5 | (a)<-[:INSTALLED_ON]-(e) WHERE e:Engine                             |              4 |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+------------+                     |
| +Filter                       |  6 | a:Aircraft                                                          |              3 |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+------------+                     |
| +Expand(All)                  |  7 | (fr)<-[:ASSIGNED_TO]-(a)                                            |              3 |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+------------+                     |
| +Filter                       |  8 | (fr:FlightRoute AND dest:Airport)                                   |              5 |            |                     |
| |                             +----+---------------------------------------------------------------------+----------------+------------+                     |
| +DirectedRelationshipTypeScan |  9 | (fr)-[:ARRIVES_AT]->(dest)                                          |              5 |            | Fused in Pipeline 0 |
+-------------------------------+----+---------------------------------------------------------------------+----------------+------------+---------------------+

Total database accesses: ?

```

### notifications_legacy (raw)

```json
[]
```

### gql_status_objects (raw)

```json
[
  {
    "gql_status": "00001",
    "status_description": "note: successful completion - omitted result",
    "raw_classification": null,
    "raw_severity": null,
    "position": null
  }
]
```

---

## groq/V2/T1 canonical/attempt0

### Cypher (as submitted, prefixed with EXPLAIN)

```cypher
MATCH (a:Aircraft)-[:ASSIGNED_TO]->(fr:FlightRoute)-[:ARRIVES_AT]->(dest:Airport)
WHERE fr.scheduled_departure >= datetime('2026-06-15T00:00:00+00:00')
  AND fr.scheduled_departure < datetime('2026-06-16T00:00:00+00:00')
WITH a, fr, dest
MATCH (a)-[:INSTALLED_ON]->(e:Engine)
WHERE e.risk_state = 'Critical'
RETURN a.tail AS aircraft, fr.flight_no AS flight, dest.icao AS dest_icao, dest.expected_wx_delay_min_per_arrival AS delay
ORDER BY delay DESC
LIMIT 5
```

### EXPLAIN error

`None`

### Plan (raw)

```
Cypher 25

Planner COST

Runtime PIPELINED

Runtime version 2026.07.1

Batch size 128

+------------------+----+------------------------------------------------------------------------------------------------------+----------------+------------+---------------------+
| Operator         | Id | Details                                                                                              | Estimated Rows | Ordered by | Pipeline            |
+------------------+----+------------------------------------------------------------------------------------------------------+----------------+------------+---------------------+
| +ProduceResults  |  0 | aircraft, flight, dest_icao, delay                                                                   |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+            |                     |
| +Projection      |  1 | a.tail AS aircraft, fr.flight_no AS flight, dest.icao AS dest_icao                                   |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+            |                     |
| +Top             |  2 | delay DESC LIMIT 5                                                                                   |              0 | delay DESC | In Pipeline 1       |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+---------------------+
| +Projection      |  3 | dest.expected_wx_delay_min_per_arrival AS delay                                                      |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +Filter          |  4 | dest:Airport                                                                                         |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +Expand(All)     |  5 | (fr)-[:ARRIVES_AT]->(dest)                                                                           |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +Filter          |  6 | (cache[fr.scheduled_departure] < RuntimeConstant(datetime($autostring_1)) AND cache[fr.scheduled_dep |              0 |            |                     |
| |                |    | arture] >= RuntimeConstant(datetime($autostring_0))) AND fr:FlightRoute                              |                |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +Expand(All)     |  7 | (a)-[:ASSIGNED_TO]->(fr)                                                                             |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +Filter          |  8 | e.risk_state = $autostring_2 AND e:Engine                                                            |              0 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +Expand(All)     |  9 | (a)-[:INSTALLED_ON]->(e)                                                                             |              3 |            |                     |
| |                +----+------------------------------------------------------------------------------------------------------+----------------+------------+                     |
| +NodeByLabelScan | 10 | a:Aircraft                                                                                           |             10 |            | Fused in Pipeline 0 |
+------------------+----+------------------------------------------------------------------------------------------------------+----------------+------------+---------------------+

Total database accesses: ?

```

### notifications_legacy (raw)

```json
[]
```

### gql_status_objects (raw)

```json
[
  {
    "gql_status": "00001",
    "status_description": "note: successful completion - omitted result",
    "raw_classification": null,
    "raw_severity": null,
    "position": null
  }
]
```

---

## groq/V2/T2 steer past filter/attempt0

### Cypher (as submitted, prefixed with EXPLAIN)

```cypher
MATCH (a:Aircraft)-[:ASSIGNED_TO]->(f:FlightRoute)-[:ARRIVES_AT]->(dest:Airport)
OPTIONAL MATCH (e:Engine)-[:INSTALLED_ON]->(a)
WITH a, f, dest, e.risk_score AS rs
ORDER BY rs DESC
WITH a, f, dest, collect(rs) AS scores
WITH a, f, dest, CASE WHEN size(scores)>0 THEN scores[0] ELSE null END AS worst_score,
     dest.expected_wx_delay_min_per_arrival AS delay
WHERE worst_score IS NOT NULL AND delay IS NOT NULL
RETURN a.tail AS tail, f.flight_no AS flight_no,
       worst_score, delay,
       worst_score * delay AS metric
ORDER BY metric DESC
```

### EXPLAIN error

`None`

### Plan (raw)

```
Cypher 25

Planner COST

Runtime PIPELINED

Runtime version 2026.07.1

Batch size 128

+-------------------------------+----+----------------------------------------------------------+----------------+-------------+---------------------+
| Operator                      | Id | Details                                                  | Estimated Rows | Ordered by  | Pipeline            |
+-------------------------------+----+----------------------------------------------------------+----------------+-------------+---------------------+
| +ProduceResults               |  0 | tail, flight_no, worst_score, delay, metric              |              1 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+             |                     |
| +Projection                   |  1 | a.tail AS tail, f.flight_no AS flight_no                 |              1 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+             |                     |
| +Sort                         |  2 | metric DESC                                              |              1 | metric DESC | In Pipeline 3       |
| |                             +----+----------------------------------------------------------+----------------+-------------+---------------------+
| +Projection                   |  3 | worst_score * delay AS metric                            |              1 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +Filter                       |  4 | worst_score IS NOT NULL AND delay IS NOT NULL            |              1 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +Projection                   |  5 | CASE                                                     |              2 |             |                     |
| |                             |    |   WHEN size(scores) > $autoint_0 THEN scores[$autoint_1] |                |             |                     |
| |                             |    |   ELSE NULL                                              |                |             |                     |
| |                             |    | END AS worst_score,                                      |                |             |                     |
| |                             |    | dest.expected_wx_delay_min_per_arrival AS delay          |                |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +EagerAggregation             |  6 | a, f, dest, collect(rs) AS scores                        |              2 |             | In Pipeline 2       |
| |                             +----+----------------------------------------------------------+----------------+-------------+---------------------+
| +Sort                         |  7 | rs DESC                                                  |              4 | rs DESC     | In Pipeline 1       |
| |                             +----+----------------------------------------------------------+----------------+-------------+---------------------+
| +Projection                   |  8 | e.risk_score AS rs                                       |              4 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +OptionalExpand(All)          |  9 | (a)<-[:INSTALLED_ON]-(e) WHERE e:Engine                  |              4 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +Filter                       | 10 | a:Aircraft                                               |              3 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +Expand(All)                  | 11 | (f)<-[:ASSIGNED_TO]-(a)                                  |              3 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +Filter                       | 12 | (f:FlightRoute AND dest:Airport)                         |              5 |             |                     |
| |                             +----+----------------------------------------------------------+----------------+-------------+                     |
| +DirectedRelationshipTypeScan | 13 | (f)-[:ARRIVES_AT]->(dest)                                |              5 |             | Fused in Pipeline 0 |
+-------------------------------+----+----------------------------------------------------------+----------------+-------------+---------------------+

Total database accesses: ?

```

### notifications_legacy (raw)

```json
[]
```

### gql_status_objects (raw)

```json
[
  {
    "gql_status": "00001",
    "status_description": "note: successful completion - omitted result",
    "raw_classification": null,
    "raw_severity": null,
    "position": null
  }
]
```

---

## groq/V2/T4 unmappable/attempt0

### Cypher (as submitted, prefixed with EXPLAIN)

```cypher
MATCH (a:Aircraft) RETURN avg(a.fuel_efficiency) AS avg_eff
```

### EXPLAIN error

`None`

### Plan (raw)

```
Cypher 25

Planner COST

Runtime PIPELINED

Runtime version 2026.07.1

Batch size 128

+-------------------+----+-----------------------------------+----------------+---------------------+
| Operator          | Id | Details                           | Estimated Rows | Pipeline            |
+-------------------+----+-----------------------------------+----------------+---------------------+
| +ProduceResults   |  0 | avg_eff                           |              1 | In Pipeline 1       |
| |                 +----+-----------------------------------+----------------+---------------------+
| +EagerAggregation |  1 | avg(a.fuel_efficiency) AS avg_eff |              1 |                     |
| |                 +----+-----------------------------------+----------------+                     |
| +NodeByLabelScan  |  2 | a:Aircraft                        |             10 | Fused in Pipeline 0 |
+-------------------+----+-----------------------------------+----------------+---------------------+

Total database accesses: ?

```

### notifications_legacy (raw)

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

### gql_status_objects (raw)

```json
[
  {
    "gql_status": "01N52",
    "status_description": "warn: property key does not exist. The property `fuel_efficiency` does not exist in database `REDACTED-INSTANCE`. Verify that the spelling is correct.",
    "raw_classification": "UNRECOGNIZED",
    "raw_severity": "WARNING",
    "position": "line: 1, column: 41, offset: 40"
  },
  {
    "gql_status": "00001",
    "status_description": "note: successful completion - omitted result",
    "raw_classification": null,
    "raw_severity": null,
    "position": null
  }
]
```

