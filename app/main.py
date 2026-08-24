from fastapi import FastAPI

app = FastAPI(title="Tasklane API")

@app.get("/health")
def health():
  return {"status": "ok"}
