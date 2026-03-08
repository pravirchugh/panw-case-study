import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.models import Incident
from app.routes.incidents import router as incidents_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "incidents_seed.json"


def seed_database():
    """Load synthetic seed data if the incidents table is empty."""
    db = SessionLocal()
    try:
        if db.query(Incident).count() > 0:
            logger.info("Database already seeded; skipping.")
            return
        if not SEED_FILE.exists():
            logger.warning("Seed file not found at %s", SEED_FILE)
            return

        with open(SEED_FILE) as f:
            items = json.load(f)

        for item in items:
            incident = Incident(
                title=item["title"],
                description=item["description"],
                category=item["category"],
                severity=item["severity"],
                status=item["status"],
                summary=item["summary"],
                checklist=json.dumps(item["checklist"]),
                ai_generated=False,
                audience_type=item.get("audience_type", "neighborhood_group"),
            )
            db.add(incident)
        db.commit()
        logger.info("Seeded %d incidents.", len(items))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="Community Guardian",
    description="AI-powered community safety and digital wellness platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(incidents_router)
