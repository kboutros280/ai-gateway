import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ΣΗΜΕΙΩΣΗ: Το OPENAI_API_KEY ΔΕΝ το βάζεις εδώ.
# Θα το ορίσουμε ως Environment Variable στο Render στο Βήμα 2.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="AI Gateway", version="1.0.0")

# CORS για να μπορεί να καλεί οτιδήποτε (θα το περιορίσεις αν θες αργότερα)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"ok": True, "service": "ai-gateway"}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Proxy προς OpenAI /v1/chat/completions.
    Δέχεται payload όπως του OpenAI και το προωθεί.
    Αναγκαστικά απενεργοποιούμε stream=True για απλότητα.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set on the server")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Απενεργοποιούμε streaming για την πρώτη έκδοση
    payload.pop("stream", None)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(connect=20.0, read=60.0, write=20.0, pool=20.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream connection error: {e!s}")

    # Αν το OpenAI γύρισε σφάλμα, προώθησέ το
    if resp.status_code >= 400:
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"error": {"message": resp.text}}
        raise HTTPException(status_code=resp.status_code, detail=err_json)

    # Κανονική επιτυχής απόκριση
    try:
        return resp.json()
    except Exception:
        # fallback
        return {"raw": resp.text}
