MATCH (e:Engine)-[:INSTALLED_ON]->(ac:Aircraft)-[:ASSIGNED_TO]->(f:FlightRoute)-[:ARRIVES_AT]->(dest:Airport)
WHERE e.risk_state = 'Critical'
WITH ac, f, dest, max(e.risk_score) AS worst_risk
WITH ac, f, dest, worst_risk,
     worst_risk * dest.expected_wx_delay_min_per_arrival AS exposure_score
ORDER BY exposure_score DESC
LIMIT 1

MATCH (sick:Engine)-[:INSTALLED_ON]->(ac)
WHERE sick.risk_score = worst_risk

MATCH (f)-[:DEPARTS_FROM]->(origin:Airport)
MATCH (spare:Aircraft)-[:LOCATED_AT]->(origin)<-[:SITUATED_AT]-(hub:MaintenanceHub)
WHERE NOT (spare)-[:ASSIGNED_TO]->(:FlightRoute)
  AND spare.ready_at + duration({minutes: hub.min_swap_duration_minutes}) <= f.scheduled_departure

RETURN f.flight_no                             AS flight,
       origin.icao                             AS departs_from,
       dest.icao                               AS arrives_at,
       dest.expected_wx_delay_min_per_arrival  AS dest_delay_risk,
       sick.engine_id                          AS engine,
       sick.risk_state                         AS engine_state,
       sick.risk_score                         AS engine_risk,
       sick.rul_cycles                         AS rul_cycles,
       exposure_score,
       spare.tail                              AS replacement_tail,
       hub.hub_code                            AS swap_at,
       spare.ready_at                          AS spare_ready,
       hub.min_swap_duration_minutes           AS swap_minutes,
       f.scheduled_departure                   AS departure