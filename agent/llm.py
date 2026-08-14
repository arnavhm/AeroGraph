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
MAX_TOOL_CALLS = 3          # 2 queries + 1 synthesis turn. Bounded on purpose.
                            # Was 2: the model gathered correct rows across two
                            # calls and then had no turn left to answer.
RPM_SLEEP_S = 13            # measured 5 RPM free-tier ceiling (429 quotaValue='5').
                            # 60/5 = 12s minimum; 13 for clock skew.

_LAST_CALL_AT = 0.0         # module-level: paces ACROSS runs, not just within one.


def _pace():
    """The gate makes 10+ separate run() calls back to back. Per-run pacing
    alone does not bound the global rate, because each run starts at
    api_calls == 0 and skips its first sleep."""
    global _LAST_CALL_AT
    elapsed = time.time() - _LAST_CALL_AT
    if elapsed < RPM_SLEEP_S:
        time.sleep(RPM_SLEEP_S - elapsed)
    _LAST_CALL_AT = time.time()

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
                    _pace()
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
                    _pace()
                resp = self.client.models.generate_content(
                    model=self.model, contents=contents, config=cfg
                )
                run.api_calls += 1
                run.final_text = (resp.text or "").strip()
        except Exception as e:
            run.error = f"{type(e).__name__}: {e}"

        # Only successful runs are cacheable. Caching an error replays it
        # forever on a key that will never miss again.
        if run.error is None:
            _cache_store(key, run, system_prompt)
        return run


# ---------------------------------------------------------------------------
# Groq provider.
#
# Added 2026-08-14. Gemini's free tier is a hard 5 RPM window: once at the
# ceiling every subsequent call 429s and a multi-test gate cannot complete
# (observed: 7 of 10 tests unreachable in one run). Groq's free tier is a
# CONTINUOUS TOKEN BUCKET - 8000 TPM refilling at ~133 tokens/sec - so pacing
# against the reported remaining balance never hits a wall.
#
# Throughput is NOT better (~4 calls/min vs Gemini's 5). Reliability is. That
# is the whole reason for this, stated plainly.
#
# Pacing reads x-ratelimit-remaining-tokens from the response headers rather
# than sleeping a guessed constant. A guessed 13s constant was tried against
# Gemini and was wrong - the quota was a rolling window, not a per-call gap.
# ---------------------------------------------------------------------------

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"

# 'low' chosen empirically 2026-08-14: correct relationship directions in 4/4
# sampled runs at ~1690 tokens. 'medium' and 'high' produced richer query
# semantics but reversed INSTALLED_ON / ASSIGNED_TO. Sample is small and the
# reasoning-quality tradeoff is unproven - revisit with more runs.
GROQ_REASONING_EFFORT = "low"


class GroqProvider:
    """Binds the one graph tool to a Groq-hosted model via manual tool calling.

    Same contract as GeminiProvider: returns an AgentRun, captures every
    generated Cypher string in Attempt objects before it reaches the database.
    The oracle in scripts/17_agent_gate.py judges rows and is provider-blind.
    """

    name = "groq"

    def __init__(self, model: str = GROQ_DEFAULT_MODEL, api_key: str | None = None,
                 reasoning_effort: str = GROQ_REASONING_EFFORT):
        from openai import OpenAI  # lazy, so non-LLM tests need no key

        self.model = model
        self.reasoning_effort = reasoning_effort
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .env (which is gitignored)."
            )
        self.client = OpenAI(api_key=key, base_url=GROQ_BASE_URL)
        # Live rate-limit state, refreshed from every response.
        self._remaining_tokens = None
        self._reset_seconds = 0.0

    # -- pacing ------------------------------------------------------------

    def _absorb_headers(self, headers):
        def num(name):
            v = headers.get(name)
            if v is None:
                return None
            v = str(v).strip()
            if v.endswith("ms"):
                return float(v[:-2]) / 1000.0
            if v.endswith("s"):
                return float(v[:-1])
            try:
                return float(v)
            except ValueError:
                return None

        rt = num("x-ratelimit-remaining-tokens")
        if rt is not None:
            self._remaining_tokens = rt
        rs = num("x-ratelimit-reset-tokens")
        if rs is not None:
            self._reset_seconds = rs

    def _wait_for_budget(self, need: int):
        """Sleep only if the bucket lacks room for the next call."""
        if self._remaining_tokens is None:
            return
        if self._remaining_tokens >= need:
            return
        # reset_tokens is the time to a FULL bucket; that is the safe bound.
        wait = self._reset_seconds + 0.5
        print(f"    [pace] remaining={self._remaining_tokens:.0f} "
              f"need~{need} sleeping {wait:.1f}s")
        time.sleep(wait)
        self._remaining_tokens = None  # unknown until the next response

    # -- main loop ---------------------------------------------------------

    def run(self, system_prompt: str, question: str, variant: str,
            use_cache: bool = True, pace: bool = True) -> AgentRun:
        import json as _json

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

        run = AgentRun(question=question, variant=variant, model=self.model)
        tools = [{"type": "function", "function": {
            "name": TOOL_NAME,
            "description": TOOL_DESCRIPTION,
            "parameters": TOOL_SCHEMA,
        }}]
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}]
        # Rough budget: prompt grows as tool results are appended.
        est = len(system_prompt) // 4 + 800

        try:
            for _ in range(MAX_TOOL_CALLS):
                if pace:
                    self._wait_for_budget(est)
                try:
                    raw = self.client.chat.completions.with_raw_response.create(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        max_completion_tokens=2000,
                        reasoning_effort=self.reasoning_effort,
                    )
                except Exception as e:
                    # Groq's tool-call parser emits malformed JSON on long
                    # multi-line Cypher (observed: a stray ']' before the
                    # closing braces). This is a serialisation failure, not a
                    # model reasoning failure, and must not discard attempts
                    # already completed successfully in this run.
                    if "tool_use_failed" not in str(e):
                        raise
                    run.api_calls += 1
                    run.attempts.append(Attempt(
                        cypher="", ok=False, row_count=0,
                        rejected_by="tool_call_serialisation",
                        error=str(e)[:400], rows=[]))
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your last tool call could not be parsed. Emit a "
                            "SHORTER, SINGLE-LINE Cypher statement with no "
                            "comments and no literal newlines."
                        ),
                    })
                    continue
                self._absorb_headers(raw.headers)
                resp = raw.parse()
                run.api_calls += 1

                msg = resp.choices[0].message
                calls = msg.tool_calls or []
                if not calls:
                    run.final_text = (msg.content or "").strip()
                    break

                tc = calls[0]
                try:
                    cypher = _json.loads(tc.function.arguments).get("query", "")
                except Exception as e:
                    cypher = ""
                    run.error = f"tool arguments not valid JSON: {e}"

                result = execute_graph_query(cypher)
                run.attempts.append(Attempt(
                    cypher=cypher,
                    ok=result["ok"],
                    row_count=result["row_count"],
                    rejected_by=result["rejected_by"],
                    error=result["error"],
                    rows=result["rows"],
                ))

                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name,
                                     "arguments": tc.function.arguments},
                    }],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": _json.dumps(result, default=str),
                })
                est += 400
            else:
                # Loop exhausted without a final answer - ask for one.
                if pace:
                    self._wait_for_budget(est)
                messages.append({
                    "role": "user",
                    "content": (
                        "You have used your query budget. Do NOT call the tool "
                        "again. Answer now in prose using ONLY the rows already "
                        "returned above. If those rows are insufficient, say so "
                        "plainly."
                    ),
                })
                raw = self.client.chat.completions.with_raw_response.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    max_completion_tokens=2000,
                    reasoning_effort=self.reasoning_effort,
                )
                self._absorb_headers(raw.headers)
                run.api_calls += 1
                fmsg = raw.parse().choices[0].message
                run.final_text = (fmsg.content or "").strip()
                if not run.final_text and (fmsg.tool_calls or []):
                    run.final_text = ""
                    run.error = "budget exhausted: model kept calling the tool instead of answering"
        except Exception as e:
            run.error = f"{type(e).__name__}: {e}"

        if run.error is None:
            _cache_store(key, run, system_prompt)
        return run


PROVIDERS = {"gemini": GeminiProvider, "groq": GroqProvider}
