# scripts/13_connect_test.py
from _env import require_venv

require_venv()
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
uri  = os.environ["NEO4J_URI"]
user = os.getenv("NEO4J_USERNAME") or os.environ["NEO4J_USER"]
pwd  = os.environ["NEO4J_PASSWORD"]
print("uri:", uri)

with GraphDatabase.driver(uri, auth=(user, pwd)) as d:
    d.verify_connectivity()
    with d.session() as s:
        rec = s.run("RETURN 1 AS ok, datetime() AS now =").single()
        print("ok:", rec["ok"], "| server time:", rec["now"])
        n = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        print("existing nodes:", n)
