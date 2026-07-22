from app.webhook.router import router as webhook_router
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
import logging
import os
import sys

print(f"Python version: {sys.version}", flush=True)
print("Starting Srisailam Pilgrim Bot...", flush=True)

logging.basicConfig(level=logging.INFO)
load_dotenv()



app = FastAPI(
    title="Srisailam Pilgrim Bot",
    description="AI WhatsApp chatbot for Srisailam temple pilgrims",
    version="1.0.0"
)

app.include_router(webhook_router)

@app.get("/health")
async def health_check():
    return {
        "status": "running",
        "bot": "Srisailam Pilgrim Bot",
        "version": "1.0.0"
    }


# ============= INTERNAL: RELIABILITY CHECK =============
from fastapi import Header, HTTPException, Depends
import hashlib
import re
import requests


async def verify_internal_key(x_internal_key: str = Header(...)):
    expected = os.getenv("INTERNAL_API_KEY")
    if not expected or x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing internal API key.")


@app.post("/internal/reliability-check", dependencies=[Depends(verify_internal_key)])
async def internal_reliability_check():
    """
    Runs the bot's own reliability suite (real devotee-question scenarios)
    and returns the report directly.
    """
    from run_pilgrim_reliability_check import run_checks
    report = run_checks()
    return {"ok": True, "report": report}


# ============= INTERNAL: PROMPT VERSION CHECK-IN =============
def _extract_prompt(file_path: str, variable_name: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(rf'{re.escape(variable_name)}\s*=\s*"""(.*?)"""', content, re.DOTALL)
    if not match:
        raise HTTPException(status_code=500, detail=f"Could not find {variable_name}")
    return match.group(1).strip()


@app.post("/internal/prompt-check", dependencies=[Depends(verify_internal_key)])
async def internal_prompt_check():
    """
    Checks all three of this bot's own prompts and reports each result
    to the observability platform's prompt registry.
    """
    prompts_to_check = [
        {"file": "app/agents/journey_planner_agent.py", "variable": "PLANNER_SYSTEM_PROMPT", "name": "pilgrim_planner_prompt"},
        {"file": "app/agents/spiritual_agent.py", "variable": "SPIRITUAL_SYSTEM_PROMPT", "name": "pilgrim_spiritual_prompt"},
        {"file": "app/rag/qa_chain.py", "variable": "SYSTEM_PROMPT", "name": "pilgrim_qa_prompt"},
    ]

    observability_url = os.getenv("OBSERVABILITY_API_URL", "http://localhost:8001/api/v1")
    internal_key = os.getenv("INTERNAL_API_KEY")
    results = []

    for p in prompts_to_check:
        try:
            base_dir = os.path.dirname(__file__)
            full_path = os.path.join(base_dir, p["file"])
            prompt_text = _extract_prompt(full_path, p["variable"])
            prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

            response = requests.post(
                f"{observability_url}/prompts/check-in",
                headers={"X-Internal-Key": internal_key},
                json={
                    "prompt_name": p["name"],
                    "prompt_hash": prompt_hash,
                    "prompt_text": prompt_text,
                    "author": "Rambhupal",
                },
                timeout=10,
            )
            response.raise_for_status()
            results.append({"prompt_name": p["name"], **response.json()})
        except Exception as e:
            results.append({"prompt_name": p["name"], "ok": False, "error": str(e)})

    return {"ok": True, "results": results}

@app.get("/")
async def root():
    return {"message": "OM NAMASIVAYA! OM SREE MATREY NAMAHA! Bot is alive."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
