# ruff: noqa: E402

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers import all_routers

app = FastAPI()
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Origin", "Cookie"],
    )

for router in all_routers:
    app.include_router(router=router, prefix="/v1")


if settings.LOG_LEVEL == "DEBUG":
    import logging
    import time

    @app.middleware("http")
    async def add_process_time_header(request, call_next):  # type: ignore[no-untyped-def] # noqa: ANN001,ANN201
        start_time = time.monotonic_ns()
        response = await call_next(request)
        process_time = (time.monotonic_ns() - start_time) / 1_000_000
        logging.debug("Response time: %.2f ms", process_time)
        return response
