"""Does gpt-oss-120b emit a structured tool call for our real tool schema?

Everything downstream depends on this. A model that writes fluent prose but
malformed tool calls is useless in the loop.
"""
import sys, pathlib, os, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _env import require_venv

require_venv()

from dotenv import load_dotenv
from openai import OpenAI
from agent.prompts import build_system_prompt
from agent.llm import TOOL_NAME, TOOL_DESCRIPTION, TOOL_SCHEMA

load_dotenv()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
client = OpenAI(api_key=os.environ["GROQ_API_KEY"],
                base_url="https://api.groq.com/openai/v1")

resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": build_system_prompt("V2")},
        {"role": "user", "content":
         "Which aircraft should we swap before its flight departs today, and "
         "which spare aircraft should replace it?"},
    ],
    tools=[{"type": "function", "function": {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "parameters": TOOL_SCHEMA,
    }}],
    max_completion_tokens=2000,
)

m = resp.choices[0].message
print(f"model: {MODEL}")
print(f"finish_reason: {resp.choices[0].finish_reason}")
print(f"content: {(m.content or '(none)')[:200]}")
print(f"reasoning field present: {hasattr(m, 'reasoning') and bool(getattr(m, 'reasoning', None))}")

tc = m.tool_calls or []
print(f"\ntool_calls: {len(tc)}")
for c in tc:
    print(f"  name: {c.function.name}")
    try:
        args = json.loads(c.function.arguments)
        print(f"  parsed OK, keys={list(args.keys())}")
        print(f"  query: {' '.join(args.get('query','').split())[:300]}")
    except Exception as e:
        print(f"  ARGS NOT VALID JSON: {e}")
        print(f"  raw: {c.function.arguments[:300]}")

u = resp.usage
print(f"\nusage: prompt={u.prompt_tokens} completion={u.completion_tokens} total={u.total_tokens}")
print(f"=> at 8000 TPM, ~{8000 // max(u.total_tokens,1)} calls/min at this size")
