from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.items import router as items_router


def create_app() -> FastAPI:
    app = FastAPI(title="Inventory Reservation System", version="1.0.0")

    app.include_router(health_router)
    app.include_router(items_router, prefix="/items", tags=["items"])

    return app


app = create_app()
