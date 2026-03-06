from fastapi import FastAPI

from backend.db.database import Base, engine
from backend.routers import auth, transactions, analytics

# Create tables on startup (use Alembic for migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance API", version="1.0.0")

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
