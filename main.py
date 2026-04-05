from fastapi import FastAPI
from app.webhook.router import router as webhook_router
from dotenv import load_dotenv
import uvicorn
import logging
import os
import sys
import asyncio
import httpx
from contextlib import asynccontextmanager

print(f"Python version: {sys.version}", flush=True)
print("Starting Srisailam Pilgrim Bot...", flush=True)

logging.basicConfig(level=logging.INFO)
load_dotenv()

RENDER_URL = "https://srisailam-pilgrim-bot-1.onrender.com"

async def keep_alive():
    while True:
        await asyncio.sleep(840)
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{RENDER_URL}/health")
                print("✅ Keep-alive ping sent", flush=True)
        except Exception as e:
            print(f"⚠️ Keep-alive failed: {e}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(keep_alive())
    yield

app = FastAPI(
    title="Srisailam Pilgrim Bot",
    description="AI WhatsApp chatbot for Srisailam temple pilgrims",
    version="1.0.0",
    lifespan=lifespan
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
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)