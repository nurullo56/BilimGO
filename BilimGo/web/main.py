from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import database
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import time
import re

from web.routers.admin_analytics import router as analytics_router
from web.routers.ai_tutor import router as ai_tutor_router
from web.routers.cabinet import router as cabinet_router
from web.routers.cards import router as cards_router
from web.routers.chat import router as chat_router
from web.routers.live import router as live_router
from web.routers.live_websocket import router as live_ws_router
from web.routers.payments import router as payments_router
from web.routers.player import router as player_router
from web.routers.quiz import router as quiz_router
from web.routers.server_expenses import router as server_expenses_router
from web.routers.users import router as users_router
from web.routers.notifications import router as notifications_router
from web.routers.waitlist import router as waitlist_router
from web.routers.feedback import router as feedback_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await database.run_migrations(settings.db.migrations_dir)
    yield
    await database.close()


app = FastAPI(title="BilimGo API", lifespan=lifespan)

# Enable CORS for React Frontend (vite/dev server on port 3000 / 5173 / any)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_router)
app.include_router(payments_router)
app.include_router(cards_router)
app.include_router(cabinet_router)
app.include_router(chat_router)
app.include_router(live_router)
app.include_router(live_ws_router)
app.include_router(analytics_router)
app.include_router(ai_tutor_router)
app.include_router(quiz_router)
app.include_router(server_expenses_router)
app.include_router(users_router)
app.include_router(notifications_router)
app.include_router(waitlist_router)
app.include_router(feedback_router)


# Search for built React frontend dist in various possible locations
candidate_paths = [
    settings.paths.frontend_dist_dir,
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent / "dist",
    Path(__file__).resolve().parent / "static",
]

STATIC_DIR = next((p for p in candidate_paths if p.exists() and (p / "index.html").exists()), Path(__file__).resolve().parent / "static")

ASSETS_DIR = STATIC_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

FALLBACK_STATIC = Path(__file__).resolve().parent / "static"
if FALLBACK_STATIC.exists() and FALLBACK_STATIC != STATIC_DIR:
    app.mount("/static", StaticFiles(directory=FALLBACK_STATIC), name="static")



@app.get("/{full_path:path}")
async def serve_mini_app_spa(full_path: str = ""):
    if full_path.startswith("api/") or full_path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        now = str(int(time.time()))
        content = re.sub(r'(/assets/[^"\'>]+\.(?:js|css))', rf'\1?v={now}', content)
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return {"message": "BilimGo API running"}

