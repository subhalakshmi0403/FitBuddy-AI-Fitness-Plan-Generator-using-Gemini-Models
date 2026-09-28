from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routes import router


BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI(

    title=settings.APP_NAME,

    description=(
        "AI-powered personalized "
        "fitness plan generator "
        "using Gemini."
    ),

    version="1.0.0",
)


# Static files
app.mount(

    "/static",

    StaticFiles(
        directory=str(
            BASE_DIR / "static"
        )
    ),

    name="static",
)


# Routes
app.include_router(router)


@app.on_event("startup")
def startup_event():

    init_db()


@app.get("/api")
def api_root():

    return {

        "application":
            settings.APP_NAME,

        "message":
            "FitBuddy API is running.",

        "docs":
            "/docs",
    }