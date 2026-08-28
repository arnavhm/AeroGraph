"""Measure Groq's real rate-limit ceiling for OUR prompt size.

Published TPM figures vary by model and go stale fast (llama-3.3-70b-versatile
was deprecated 2026-06-17). The only number that matters is the one the API
reports for the prompt we actually send, which carries the full graph schema.
"""
import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _env import require_venv

require_venv()

from dotenv import load_dotenv
from openai import OpenAI
from agent.prompts import build_system_prompt

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

key = os.getenv("GROQ_API_KEY")
if not key:
    sys.exit("GROQ_API_KEY not set in .env")

sp = build_system_prompt("V2")
print(f"model: {MODEL}")
print(f"system prompt chars: {len(sp)}  (~{len(sp)//4} tokens, rough)")

client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

try:
    resp = client.chat.completions.with_raw_response.create(
        model=MODEL,
        messages=[{"role": "system", "content": sp},
                  {"role": "user", "content": "Reply with the single word: ok"}],
        max_tokens=10,
    )
except Exception as e:
    sys.exit(f"CALL FAILED: {type(e).__name__}: {e}")

h = resp.headers
print("\n--- rate limit headers ---")
found = False
for k in sorted(h.keys()):
    if "ratelimit" in k.lower():
        print(f"  {k}: {h[k]}")
        found = True
if not found:
    print("  (none returned)")

parsed = resp.parse()
print(f"\nreply: {parsed.choices[0].message.content!r}")
u = parsed.usage
print(f"usage: prompt={u.prompt_tokens} completion={u.completion_tokens} total={u.total_tokens}")

lim_t = h.get("x-ratelimit-limit-tokens")
lim_r = h.get("x-ratelimit-limit-requests")
if lim_t:
    per_min = int(lim_t) // max(u.total_tokens, 1)
    print(f"\nTPM {lim_t} / {u.total_tokens} tokens per call => ~{per_min} calls/min before TPM binds")
    if lim_r:
        print(f"RPM limit: {lim_r}")
        print(f"BINDING CONSTRAINT: {'TPM' if per_min < int(lim_r) else 'RPM'} "
              f"=> ~{min(per_min, int(lim_r))} calls/min")
