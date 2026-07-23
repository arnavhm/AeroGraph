import sys, pathlib

EXPECTED = "aerograph"

def require_venv():
    if pathlib.Path(sys.prefix).name != EXPECTED:
        sys.exit(f"WRONG ENV: running under {sys.prefix}\n"
                 f"Expected .venvs/{EXPECTED}. Activate it and rerun.")
