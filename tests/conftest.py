import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.in_memory.item_repo import InMemoryItemRepository
from app.services.item_service import ItemService
from app.routes.items import router as items_router


@pytest.fixture
def item_repo() -> InMemoryItemRepository:
    return InMemoryItemRepository()


@pytest.fixture
def item_service(item_repo: InMemoryItemRepository) -> ItemService:
    return ItemService(repository=item_repo)


@pytest.fixture
def client(item_service: ItemService) -> TestClient:
    app = create_app()
    # Override dependency so routes use the test-scoped service
    from app.routes import items as items_module
    app.dependency_overrides[items_module.get_item_service] = lambda: item_service
    return TestClient(app)
