"""FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Load backend/.env. override=True means the values in .env always win,
# even if the same name is already set (for example empty) in Windows.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from app.database.connection import init_db  # noqa: E402
from app.routes import auth, history, interviews, progress  # noqa: E402
from app.services import ai_service  # noqa: E402

logger = logging.getLogger(__name__)

# The built website (made by "npm run build"). When this folder exists, this server also
# serves the website, so the whole project runs from one address (used for deployment).
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI-Powered Mock Interview API",
    version="1.0.0",
    description="Practice interviews with AI feedback, adaptive follow-ups and progress tracking.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip()],
    # Any port on localhost / 127.0.0.1 is allowed, so Edge, Chrome and Vite never get blocked.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(interviews.router)
app.include_router(history.router)
app.include_router(progress.router)


@app.get("/api/health", tags=["system"])
def health() -> dict:
    """Tells the frontend whether an AI service is configured or the app is in demo mode."""
    return {
        "status": "ok",
        "ai_mode": "gemini" if ai_service.is_ai_configured() else "demo",
    }


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"] if part != "body")
        message = str(error["msg"]).replace("Value error, ", "")
        messages.append(f"{field}: {message}" if field else message)
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Unexpected server error. Please try again."},
    )


def find_frontend_file(dist: Path, url_path: str) -> Optional[Path]:
    """The file inside the built website for this URL, or None (never outside the folder)."""
    if not url_path:
        return None
    root = dist.resolve()
    candidate = (root / url_path).resolve()
    if candidate.is_file() and candidate.is_relative_to(root):
        return candidate
    return None


if FRONTEND_DIST.is_dir():
    # Deployment: serve the website from this same server. This block must stay LAST,
    # so the /api routes and /docs above are matched first.
    @app.get("/{url_path:path}", include_in_schema=False)
    def serve_website(url_path: str):
        if url_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        file = find_frontend_file(FRONTEND_DIST, url_path)
        if file is not None:
            return FileResponse(file)
        # Pages such as /history or /privacy are handled by React: always send index.html.
        return FileResponse(FRONTEND_DIST / "index.html")

else:

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        """Opening http://127.0.0.1:8000 in a browser shows the API docs, not an error."""
        return RedirectResponse(url="/docs")