"""Application FastAPI — AI Class Attendance for Students."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from . import web
from .auth import Forbidden, NotAuthenticated, ensure_default_users
from .database import SessionLocal, init_db
from .routers import academics, attendance, reports, students


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        ensure_default_users(db)   # crée admin + enseignant au 1er démarrage
    finally:
        db.close()
    yield


app = FastAPI(
    title="AI Class Attendance for Students",
    version="0.1.0",
    lifespan=lifespan,
)

# Session (cookie signé) pour la connexion
app.add_middleware(SessionMiddleware, secret_key="isga-pfa-session-secret-2025")


@app.exception_handler(NotAuthenticated)
async def _not_authenticated(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
async def _forbidden(request: Request, exc: Forbidden):
    return RedirectResponse("/", status_code=303)


app.include_router(students.router)
app.include_router(academics.router)
app.include_router(attendance.router)
app.include_router(reports.router)
app.include_router(web.router)  # dashboard (sert la racine "/")


@app.get("/health", tags=["service"])
def health():
    return {"service": "AI Class Attendance for Students", "status": "ok"}
