from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.routes.user import router as user_router
from src.db.config import Base, engine
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="IoT API",
    description="API for the IoT project",
    lifespan=lifespan
)

# Include routers
app.include_router(user_router)

@app.get("/")
async def test():
    return {"message": "API is running successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
