"""Tiny FastAPI support-ticket service.

The point of this demo is the CI/CD pipeline around the app —
the application logic is deliberately minimal and stays in-memory.
"""

from fastapi import FastAPI

from app.routers import support

app = FastAPI(title="support-api", version="0.1.1")
app.include_router(support.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
