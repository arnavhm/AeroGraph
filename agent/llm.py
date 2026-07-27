"""
The LLM binding layer - the ONLY module that knows what an LLM is.

agent/graph_tool.py, agent/guardrails.py and agent/schema_builder.py contain
zero provider-specific code. Swapping Gemini for Groq / OpenRouter / a local
model is a change to THIS FILE ONLY. That is deliberate: it buys provider
optionality without committing to a provider swap now, which would deviate
from charter section 7 ("bound to Gemini 2.5 Flash") and needs a logged
decision rather than momentum.

Automatic function calling is DISABLED. The loop is driven manually so every
Cypher string the model produces is captured, validated and logged before it
reaches the database. With automatic FC the SDK would call the tool for us and
the generated Cypher would never be inspected - unacceptable for a project
whose entire thesis is verifiable control over what reaches the graph.
"""
import hashlib
import json
import os
import pathlib
import time
from dataclasses import dataclass, field, asdict

from dotenv import load_dotenv

from agent.graph_tool import execute_graph_query

load_dotenv()

CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / ".agent_cache"
MAX_TOOL_CALLS = 2          # 1 initial attempt + 1 correction. Bounded on purpose.
RPM_SLEEP_S = 7             # paces calls under a 10 RPM free-tier ceiling.

TOOL_NAME = "execute_graph_query"
TOOL_DESCRIPTION = (
    "Run a single READ-ONLY Cypher query against the AeroGraph knowledge graph "
    "and return the resulting rows. Rejects any query that attempts to create, "
    "modify or delete data."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "A single read-only Cypher statement.",
        }
    },
    "required": ["query"],
}


@dataclass
class Attempt:
    cypher: str
    ok: bool
    row_count: int
    rejected_by: str | None
    error: str | None
    rows: list = field(default_factory=list)


@dataclass
class AgentRun:
    question: str
    variant: str
    model: str
    attempts: list = field(default_factory=list)
    final_text: str = ""
    api_calls: int = 0
    cached: bool = False
    error: str | None = None

    def to_dict(self):
        d = asdict(self)
        return d


def _cache_key(provider: str, model: str, system_prompt: str, question: str) -> str:
    blob = "\x00".join([provider, model, system_prompt, question]).encode()
    return hashlib.sha256(blob).hexdigest()[:24]


def _cache_load(key: str):
    p = CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _cache_store(key: str, run: AgentRun, system_prompt: str):
    CACHE_DIR.mkdir(exist_ok=True)
    payload = run.to_dict()
    payload["_system_prompt_sha256"] = hashlib.sha256(system_prompt.encode()).hexdigest()
    payload["_stored_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (CACHE_DIR / f"{key}.json").write_text(json.dumps(payload, indent=2, default=str))


class GeminiProvider:
    """Binds the one graph tool to Gemini 2.5 Flash via manual function calling."""

    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        from google import genai  # imported lazily so non-LLM tests need no key

        self.model = model
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to .env (which is gitignored)."
            )
        self.client = genai.Client(api_key=key)

    def _config(self, system_prompt: str):
        from google.genai import types

        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=TOOL_NAME,
                            description=TOOL_DESCRIPTION,
                            parameters_json_schema=TOOL_SCHEMA,
                        )
                    ]
                )
            ],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    def run(self, system_prompt: str, question: str, variant: str,
            use_cache: bool = True, pace: bool = True) -> AgentRun:
        key = _cache_key(self.name, self.model, system_prompt, question)
        if use_cache:
            hit = _cache_load(key)
            if hit:
                run = AgentRun(question=question, variant=variant, model=self.model)
                run.attempts = [Attempt(**a) for a in hit.get("attempts", [])]
                run.final_text = hit.get("final_text", "")
                run.api_calls = hit.get("api_calls", 0)
                run.error = hit.get("error")
                run.cached = True
                return run

        from google.genai import types

        run = AgentRun(question=question, variant=variant, model=self.model)
        cfg = self._config(system_prompt)
        contents = [types.Content(role="user", parts=[types.Part(text=question)])]

        try:
            for _ in range(MAX_TOOL_CALLS):
                if pace and run.api_calls:
                    time.sleep(RPM_SLEEP_S)
                resp = self.client.models.generate_content(
                    model=self.model, contents=contents, config=cfg
                )
                run.api_calls += 1

                calls = resp.function_calls or []
                if not calls:
                    run.final_text = (resp.text or "").strip()
                    break

                fc = calls[0]
                cypher = (fc.args or {}).get("query", "")
                result = execute_graph_query(cypher)
                run.attempts.append(
                    Attempt(
                        cypher=cypher,
                        ok=result["ok"],
                        row_count=result["row_count"],
                        rejected_by=result["rejected_by"],
                        error=result["error"],
                        rows=result["rows"],
                    )
                )

                contents.append(resp.candidates[0].content)
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_function_response(
                            name=fc.name, response=result)],
                    )
                )
            else:
                # Loop exhausted without the model producing a final answer.
                if pace:
                    time.sleep(RPM_SLEEP_S)
                resp = self.client.models.generate_content(
                    model=self.model, contents=contents, config=cfg
                )
                run.api_calls += 1
                run.final_text = (resp.text or "").strip()
        except Exception as e:
            run.error = f"{type(e).__name__}: {e}"

        _cache_store(key, run, system_prompt)
        return run
