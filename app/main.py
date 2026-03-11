from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import coach, sessions, commands, scenarios
from app.core.database import init_db

app = FastAPI(
    title="LLM Coach API",
    description="K8s 운영 학습 코치 - Chaos Scenario + RAG + LLM Hint",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(coach.router,     prefix="/coach",    tags=["coach"])
app.include_router(sessions.router,  prefix="/session",  tags=["session"])
app.include_router(commands.router,  prefix="/command",  tags=["command"])
app.include_router(scenarios.router, prefix="/scenario", tags=["scenario"])

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}