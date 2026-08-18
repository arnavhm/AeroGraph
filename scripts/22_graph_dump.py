# scripts/22_graph_dump.py
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _env import require_venv

require_venv()

from agent.db import get_driver

def get_name(label, props):
    if label == "Airport": return props.get("icao", "Unknown")
    if label == "MaintenanceHub": return props.get("hub_code", "Unknown")
    if label == "Aircraft": return props.get("tail", "Unknown")
    if label == "Engine": return str(props.get("engine_id", "Unknown"))
    if label == "FlightRoute": return props.get("flight_no", "Unknown")
    return "Unknown"

def main():
    drv = get_driver()
    nodes = []
    links = []

    with drv.session(default_access_mode="READ") as s:
        # Get nodes
        res_nodes = s.run("MATCH (n) RETURN elementId(n) AS id, labels(n)[0] AS label, n AS props")
        for r in res_nodes:
            nid = r["id"]
            label = r["label"]
            name = get_name(label, r["props"])
            nodes.append({"id": nid, "label": label, "name": name})

        # Get links
        res_links = s.run("MATCH (a)-[r]->(b) RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type")
        for r in res_links:
            links.append({"source": r["source"], "target": r["target"], "type": r["type"]})

    print(f"Nodes: {len(nodes)}")
    print(f"Links: {len(links)}")

    if len(nodes) != 38 or len(links) != 42:
        print("ERROR: Node or link count mismatch! Expected 38 nodes, 42 links.")
        sys.exit(1)

    out_path = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "public" / "graph.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"nodes": nodes, "links": links}, f, indent=2)

if __name__ == "__main__":
    main()
