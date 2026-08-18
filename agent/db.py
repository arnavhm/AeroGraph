"""Single place that knows how to reach Neo4j. Read-only by construction."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

_driver = None


def get_driver():
    """Lazily build the shared driver. Same env-key fallback as scripts/15_gate.py."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(
                os.getenv("NEO4J_USERNAME") or os.environ["NEO4J_USER"],
                os.environ["NEO4J_PASSWORD"],
            ),
            max_connection_lifetime=200,
        )
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
