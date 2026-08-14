"""Prove the oracle catches what the old one missed. No DB, no API key."""
import sys, pathlib, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _env import require_venv

require_venv()

from agent.llm import AgentRun, Attempt

_spec = importlib.util.spec_from_file_location(
    "gate", pathlib.Path(__file__).resolve().parent / "17_agent_gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def mk(rows_per_attempt, error=None):
    r = AgentRun(question="q", variant="V1", model="test")
    r.error = error
    for rows in rows_per_attempt:
        r.attempts.append(Attempt(cypher="MATCH (n) RETURN n", ok=True,
                                  row_count=len(rows), rejected_by=None,
                                  error=None, rows=rows))
    return r


CASES = [
    ("correct answer",
     mk([[{"flight": "AG101", "spare": "G-AGSA",
           "exposure_score": 1.010777147894676}]]), "PASS"),
    ("THE SESSION 3 FALSE POSITIVE - values present, wrong pairing",
     mk([[{"flight": "AG103", "spare": "G-AGSA", "score": 1.010777147894676},
          {"flight": "AG101", "spare": "D-AGSC", "score": 0.5}]]), "FAIL"),
    ("CO-OCCURRENCE, trap-free: golden values scattered across rows in ONE query",
     mk([[{"flight": "AG104", "spare": "G-AGSA", "score": 1.010777147894676},
          {"flight": "AG101", "spare": "SE-AGDD", "score": 0.131}]]), "FAIL"),
    ("OPTION A: trap in exploratory attempt, filtered out of final - must PASS",
     mk([[{"flight": "AG101"}, {"flight": "AG103"}],
         [{"flight": "AG101", "spare": "G-AGSA",
           "exposure_score": 1.010777147894676}]]), "PASS"),
    ("OPTION A: trap survives into final attempt - must FAIL",
     mk([[{"flight": "AG101"}],
         [{"flight": "AG103", "spare": "G-AGSA",
           "exposure_score": 1.010777147894676}]]), "FAIL"),
    ("reversed direction - valid query, 0 rows",
     mk([[]]), "FAIL"),
    ("trap flight surfaces",
     mk([[{"flight": "AG103", "spare": "G-AGSA",
           "exposure_score": 1.010777147894676}]]), "FAIL"),
    ("near-miss spare offered",
     mk([[{"flight": "AG101", "spare": "G-AGSB",
           "exposure_score": 1.010777147894676}]]), "FAIL"),
    ("split across two queries - not a pass, needs eyes",
     mk([[{"flight": "AG101", "exposure_score": 1.010777147894676}],
         [{"spare": "G-AGSA"}]]), "SPLIT"),
    ("column names differ - must not matter",
     mk([[{"tail_to_swap": "AG101", "replacement": "G-AGSA",
           "risk_x_delay": 1.010777147894676}]]), "PASS"),
    ("float formatted as string",
     mk([[{"f": "AG101", "s": "G-AGSA", "e": "1.010777147894676"}]]), "PASS"),
    ("API never reached",
     mk([], error="ResourceExhausted: 429"), "ERROR"),
]

fails = 0
for name, run, expected in CASES:
    got, note = gate.judge_canonical(run)
    ok = got == expected
    fails += not ok
    print(f"[{'ok ' if ok else 'BAD'}] {name:52} want={expected:8} got={got:8} {note[:70]}")

print(f"\nORACLE SELFTEST {'PASS' if not fails else f'FAIL ({fails})'}")
sys.exit(1 if fails else 0)
