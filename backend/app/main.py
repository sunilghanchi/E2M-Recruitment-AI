from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import match
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Recruitment AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
