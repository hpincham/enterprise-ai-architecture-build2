import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.openai_client import get_aoai_client

load_dotenv()  # loads .env for local dev

app = FastAPI(title="Enterprise AI Gateway (Build 2)")

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=200, ge=1, le=800)

@app.get("/health")
def health():
    return {"status": "ok", "build": 2}

@app.post("/chat")
def chat(body: ChatRequest):
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_DEPLOYMENT not set")

    client = get_aoai_client()

    resp = client.chat.completions.create(
        model=deployment,  # Azure uses DEPLOYMENT NAME here
        messages=[{"role": "user", "content": body.prompt}],
        max_tokens=body.max_tokens,
    )

    return {
        "response": resp.choices[0].message.content,
        "model": deployment,
    }
