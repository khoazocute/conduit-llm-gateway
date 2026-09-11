from fastapi import FastAPI

app = FastAPI(title="Conduit AI Service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
