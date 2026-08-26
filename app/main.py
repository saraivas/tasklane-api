from fastapi import FastAPI
from app.routers import auth, tasks


app = FastAPI(title="Tasklane API")

app.include_router(auth.router)
app.include_router(tasks.router)

@app.get("/health")
def health():
  return {"status": "ok"}
