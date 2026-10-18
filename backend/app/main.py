"""
FastAPI application entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import variant, demo, pathway, simulation

app = FastAPI(
    title="SNPs to Pathways API",
    description="Integrates variant-level functional effects into cell signalling pathway models.",
    version="0.1.0",
)

# Allow the Vite dev server (default port 5173) to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(variant.router)
app.include_router(demo.router)
app.include_router(pathway.router)
app.include_router(simulation.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
