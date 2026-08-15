"""
Action catalog for AeroGraph.

Defines parameterized, pre-approved Cypher actions, their parameter schemas,
and validation logic. Decouples action definitions from execution.
"""
import pathlib

ACTIONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "cypher" / "actions"

ACTIONS = {
    "worst_exposure_swap": {
        "description": (
            "Find the flight whose destination delay risk and worst engine "
            "risk combine to the highest exposure, and the spare aircraft "
            "that can replace it in time."
        ),
        "cypher_file": "worst_exposure_swap.cypher",
        "params": {
            "risk_state": {
                "type": "string",
                "enum": ["Critical", "Degrading", "Healthy"],
                "default": "Critical",
            },
            "limit": {
                "type": "integer",
                "min": 1,
                "max": 5,
                "default": 1,
            },
        },
    },
}


def load_cypher(action_name: str) -> str:
    """Read action Cypher statement from cypher/actions/."""
    if action_name not in ACTIONS:
        raise KeyError(f"unknown action {action_name!r}")
    filename = ACTIONS[action_name]["cypher_file"]
    path = ACTIONS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"cypher file not found: {path}")
    return path.read_text().strip()


def validate_params(action_name: str, params: dict | None) -> tuple[bool, str, dict]:
    """Validate parameters against action schema and populate defaults.

    Returns:
        (ok, reason, resolved)
    """
    if action_name not in ACTIONS:
        return False, f"unknown action {action_name!r}", {}

    if params is None:
        params = {}
    elif not isinstance(params, dict):
        return False, f"params must be a dict, got {type(params).__name__}", {}

    spec = ACTIONS[action_name]["params"]

    # Check for unknown parameters
    for k in params:
        if k not in spec:
            return False, f"unknown parameter key {k!r}", {}

    resolved = {}
    for pname, pdef in spec.items():
        if pname in params:
            val = params[pname]
        elif "default" in pdef:
            val = pdef["default"]
        else:
            return False, f"missing required parameter {pname!r}", {}

        ptype = pdef.get("type")
        if ptype == "integer":
            if isinstance(val, bool):
                return False, f"parameter {pname!r} expected integer, got bool", {}
            if not isinstance(val, int):
                return False, f"parameter {pname!r} expected integer, got {type(val).__name__}", {}
            if "min" in pdef and val < pdef["min"]:
                return False, f"parameter {pname!r} value {val} below min {pdef['min']}", {}
            if "max" in pdef and val > pdef["max"]:
                return False, f"parameter {pname!r} value {val} above max {pdef['max']}", {}
        elif ptype == "string":
            if not isinstance(val, str):
                return False, f"parameter {pname!r} expected string, got {type(val).__name__}", {}
            if "enum" in pdef and val not in pdef["enum"]:
                return False, f"parameter {pname!r} value {val!r} not in enum {pdef['enum']}", {}
        else:
            # Unsupported type in spec
            return False, f"unsupported schema type {ptype!r} for parameter {pname!r}", {}

        resolved[pname] = val

    return True, "", resolved
