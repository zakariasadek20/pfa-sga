"""Application FastAPI — AI Class Attendance for Students."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import web
from .database import init_db
from .routers import academics, attendance, reports, students


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Class Attendance for Students",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(students.router)
app.include_router(academics.router)
app.include_router(attendance.router)
app.include_router(reports.router)
app.include_router(web.router)  # dashboard (sert la racine "/")


@app.get("/health", tags=["service"])
def health():
    return {"service": "AI Class Attendance for Students", "status": "ok"}
