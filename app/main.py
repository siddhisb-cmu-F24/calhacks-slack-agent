"""FastAPI application bootstrap."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .config import settings
from .deps import shutdown_dependencies
from .domain.schemas import ProblemDetails
from .routers import health, memory, slack


@asynccontextmanager
def lifespan(_: FastAPI):
    yield
    await shutdown_dependencies()


app = FastAPI(title="Slack Q&A Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "https://www.postman.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(memory.router)
app.include_router(slack.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.debug("validation error: {}", exc.errors())
    detail = ProblemDetails(
        title="Invalid Request",
        detail="Input validation failed",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    return JSONResponse(status_code=detail.status, content=detail.model_dump())


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "slack-agent", "status": "ok"}
