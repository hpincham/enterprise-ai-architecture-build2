import time
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Enterprise AI Gateway (Build 2)")
log = logging.getLogger("enterprise-ai-gateway")

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=200, ge=1, le=800)

@app.get("/health")
def health():
    return {"status": "ok", "build": 2}

@app.post("/chat")
async def chat(req: Request, body: ChatRequest):
    if len(body.prompt) > 4000:
        raise HTTPException(status_code=400, detail="Prompt too long")

    # Stubbed response for now
    return {"response": f"[stubbed] You said: {body.prompt}", "model": "stub"}
