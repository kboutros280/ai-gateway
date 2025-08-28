from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

# Παίρνει το API key από το Render (Environment Variable)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )
    return response.json()
