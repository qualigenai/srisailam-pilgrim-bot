from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from app.webhook.router import router as webhook_router

load_dotenv()

app = FastAPI(
    title="Srisailam Pilgrim Bot",
    description="AI WhatsApp chatbot for Srisailam temple pilgrims",
    version="1.0.0"
)

# Include webhook router
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
    return {"message": "Jai Mallikarjuna! Bot is alive."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)