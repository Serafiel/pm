import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(os.environ.get("STATIC_DIR", "/app/static"))

app = FastAPI()


@app.get("/api/ping")
async def ping():
    return {"status": "ok"}


app.mount("/_next", StaticFiles(directory=str(STATIC_DIR / "_next")), name="assets")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse(str(STATIC_DIR / "index.html"))
