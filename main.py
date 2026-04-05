from fastapi import FastAPI
from app.webhook.router import router as webhook_router
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

@app.get("/")
async def root():
    return {"message": "OM NAMASIVAYA! OM SREE MATREY NAMAHA! Bot is alive."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)