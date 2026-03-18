import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from fetcher.cleanup import check_and_cleanup
from fetcher.scheduler import start_scheduler, stop_scheduler, _check_startup_catchup
from api.articles import router as articles_router
from api.sources import router as sources_router
from api.briefings import router as briefings_router
from api.fetch import router as fetch_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await check_and_cleanup()
    start_scheduler()
    # Don't block startup with catch-up fetch — run in background
    # asyncio.create_task(_check_startup_catchup())
    yield
    stop_scheduler()


app = FastAPI(title="AI Dynamics", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(sources_router)
app.include_router(briefings_router)
app.include_router(fetch_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9100, reload=True)
