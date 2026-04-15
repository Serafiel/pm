from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>hello world</h1>"


@app.get("/api/ping")
async def ping():
    return {"status": "ok"}
