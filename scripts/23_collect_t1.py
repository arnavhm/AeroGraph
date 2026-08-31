import argparse
import time
import datetime
import urllib.request
import urllib.error
import json
import sys
import os
import importlib.util

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    spec_env = importlib.util.spec_from_file_location("_env", os.path.join(project_root, "scripts", "_env.py"))
    _env = importlib.util.module_from_spec(spec_env)
    spec_env.loader.exec_module(_env)
    _env.require_venv()
except Exception:
    pass

gate_path = os.path.join(project_root, "scripts", "17_agent_gate.py")
spec = importlib.util.spec_from_file_location("agent_gate", gate_path)
agent_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_gate)
TESTS = agent_gate.TESTS

T1_QUESTION = next((q for tid, q in TESTS if tid.startswith("T1")), None)
if T1_QUESTION is None:
    sys.exit("FATAL: Could not find T1 question in TESTS")

def main():
    parser = argparse.ArgumentParser(description="Collect T1 observations")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs")
    parser.add_argument("--provider", type=str, default="groq", help="LLM Provider")
    parser.add_argument("--out-dir", type=str, default="t1_runs",
                        help="Subdirectory under data/interim/")
    args = parser.parse_args()

    out_dir = os.path.join(project_root, "data", "interim", args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    url = "http://localhost:8000/ask"

    for i in range(1, args.runs + 1):
        payload = {
            "question": T1_QUESTION,
            "variant": "V2",
            "provider": args.provider,
            "use_cache": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data,
            headers={"Content-Type": "application/json"}
        )

        start_time = time.time()
        start_dt = datetime.datetime.now()
        
        status = None
        body = b""
        
        try:
            with urllib.request.urlopen(req) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read()
        except urllib.error.URLError as e:
            print(f"{i} ERR {e.reason}")
            continue

        elapsed_ms = int((time.time() - start_time) * 1000)
        
        cached_val = None
        resp_json = None
        try:
            resp_json = json.loads(body.decode("utf-8"))
            cached_val = resp_json.get("cached")
        except Exception:
            pass

        print(f"{i} {status} {cached_val}")

        ts_str = start_dt.strftime("%Y%m%d_%H%M%S")
        filename = f"run_{i:03d}_{ts_str}.json"
        filepath = os.path.join(out_dir, filename)
        
        artifact = {
            "_meta": {
                "timestamp": start_dt.isoformat(),
                "elapsed_ms": elapsed_ms
            },
            "response": resp_json if resp_json is not None else body.decode("utf-8", errors="replace")
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2)

        if cached_val is True:
            print(f"ABORT: Run {i} returned cached: true with use_cache: false")
            break

if __name__ == "__main__":
    main()
