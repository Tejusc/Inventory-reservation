from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.health import router as health_router
from app.routes.items import router as items_router
from app.routes.reservations import router as reservations_router

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Inventory Reservation System", version="1.0.0")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    app.include_router(health_router)
    app.include_router(items_router, prefix="/items", tags=["items"])
    app.include_router(reservations_router, prefix="/reservations", tags=["reservations"])

    @app.get("/", include_in_schema=False)
    def ui() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
