"""
AeroGraph Layer 3 backend - FastAPI.

Routes:
  POST /query   exposes execute_graph_query directly (the tool itself; also what
                the criterion-5 graph visualisation will consume).
  POST /ask     natural language -> selected provider (agent.llm.PROVIDERS,
                default groq) -> generated Cypher -> guardrails -> graph ->
                natural-language answer. This is the criterion-3 demo surface.
  POST /action  runs a pre-approved parameterised catalog action via
                agent.action_tool.execute_action (Option D). Same response
                shape as /query; never raises to the caller.
  GET  /actions discovery: the catalog's action names, descriptions, and
                parameter schemas. cypher_file is deliberately not exposed —
                filesystem paths do not belong in an API response.

Explicitly NOT here, per the active scope fence: no auth, no multi-user, no
chat history, no second query type. One request, one answer.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph_tool import execute_graph_query
from agent.prompts import build_system_prompt

app = FastAPI(title="AeroGraph Layer 3", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryIn(BaseModel):
    query: str


class AskIn(BaseModel):
    question: str
    variant: str = "V2"
    use_cache: bool = True
    provider: str = "groq"


class ActionIn(BaseModel):
    action: str
    params: dict | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(body: QueryIn):
    """Run a read-only Cypher statement. Guardrailed; never raises to the caller."""
    return execute_graph_query(body.query)


@app.post("/action")
def action(body: ActionIn):
    """Run a pre-approved parameterised action. Guardrailed by the catalog."""
    from agent.action_tool import execute_action
    return execute_action(body.action, body.params)


@app.get("/actions")
def actions():
    """List available actions and their parameter schemas."""
    from agent.catalog import ACTIONS
    return {name: {"description": spec["description"], "params": spec["params"]}
            for name, spec in ACTIONS.items()}


@app.post("/ask")
def ask(body: AskIn):
    """Natural-language question -> tool-using LLM -> grounded answer."""
    from agent.llm import PROVIDERS
    from agent.prompts import VALID_VARIANTS
    from fastapi.responses import JSONResponse

    if body.variant not in VALID_VARIANTS:
        return JSONResponse(status_code=400, content={"error": f"Invalid variant {body.variant!r}. Valid variants are: {VALID_VARIANTS}"})

    if body.provider not in PROVIDERS:
        return JSONResponse(status_code=400, content={"error": f"Invalid provider {body.provider!r}. Valid providers are: {sorted(PROVIDERS)}"})

    try:
        provider = PROVIDERS[body.provider]()
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    system_prompt = build_system_prompt(body.variant)
    run = provider.run(system_prompt, body.question, body.variant,
                       use_cache=body.use_cache)
    return {
        "ok": run.error is None,
        "question": run.question,
        "variant": run.variant,
        "provider": provider.name,
        "model": run.model,
        "cached": run.cached,
        "api_calls": run.api_calls,
        "answer": run.final_text,
        "attempts": [
            {"cypher": a.cypher, "ok": a.ok, "row_count": a.row_count,
             "rejected_by": a.rejected_by, "error": a.error}
            for a in run.attempts
        ],
        "rows": run.attempts[-1].rows if run.attempts else [],
        "error": run.error,
    }
